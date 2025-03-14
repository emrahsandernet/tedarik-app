import operator
from django.core.exceptions import ValidationError
import json
from decimal import Decimal

class ConditionEngine:
    OPERATORS = {
        '>': operator.gt,
        '<': operator.lt,
        '>=': operator.ge,
        '<=': operator.le,
        '==': operator.eq,
        '!=': operator.ne,
        'in': lambda a, b: a in b,
        'contains': operator.contains,
        'startswith': lambda a, b: a.startswith(b) if hasattr(a, 'startswith') else False,
        'endswith': lambda a, b: a.endswith(b) if hasattr(a, 'endswith') else False,
    }
    
    def __init__(self, context: dict):
        self.context = context  # {order: PurchaseOrder, user: User, ...}

    def evaluate(self, condition: dict) -> bool:
        """Örnek koşul yapısı:
        {
            "field": "total_amount",
            "operator": ">",
            "value": 10000,
            "logic": "AND"  # VEYA "OR" için nested conditions
        }
        
        Veya nested conditions için:
        {
            "conditions": [
                {"field": "order.toplam_tutar", "operator": ">", "value": 5000},
                {"field": "order.olusturan.username", "operator": "==", "value": "sandernet1"}
            ],
            "logic": "AND"
        }
        """
        if isinstance(condition, str):
            try:
                condition = json.loads(condition)
            except:
                raise ValidationError(f"Invalid condition format: {condition}")
        
        # Eğer conditions alanı varsa, nested conditions olarak değerlendir
        if 'conditions' in condition and isinstance(condition['conditions'], list):
            logic = condition.get('logic', 'AND').upper()
            results = [self.evaluate(cond) for cond in condition['conditions']]
            
            if logic == 'AND':
                return all(results)
            elif logic == 'OR':
                return any(results)
            else:
                raise ValidationError(f"Unknown logic operator: {logic}")
        
        # Eğer field alanı varsa, basit koşul olarak değerlendir
        elif 'field' in condition:
            try:
                field_path = condition.get('field', '')
                operator_str = condition.get('operator', '>')
                value = condition.get('value', 0)
                
                # Field değerini al
                field_value = self._get_field_value(field_path)
                print(f"Evaluating condition: {condition}, field_value: {field_value}")
                
                # Değer dönüşümü
                value = self._convert_value(field_value, value)
                
                # Operatörü uygula
                return self._apply_operator(operator_str, field_value, value)
            except (KeyError, AttributeError) as e:
                print(f"Error in condition evaluation: {str(e)}")
                raise ValidationError(f"Invalid condition: {str(e)}")
        
        # Ne conditions ne de field alanı varsa, hata döndür
        else:
            raise ValidationError(f"Invalid condition format: {condition}")

    def _get_field_value(self, field_path):
        """Field değerini alır"""
        if not field_path:
            raise AttributeError("Field path cannot be empty")
            
        # Genel field yolu çözümleme
        try:
            return self._get_nested_attr(self.context, field_path)
        except (AttributeError, KeyError) as e:
            print(f"Error getting field value for {field_path}: {str(e)}")
            raise AttributeError(f"Unknown field path: {field_path}")

    def _convert_value(self, field_value, value):
        """Değeri field değerine uygun tipe dönüştürür"""
        if isinstance(field_value, (int, float, Decimal)):
            try:
                return float(value)
            except (ValueError, TypeError):
                return value
        elif isinstance(field_value, bool):
            if isinstance(value, str):
                return value.lower() in ('true', 'yes', '1', 'on')
            return bool(value)
        elif isinstance(field_value, str):
            return str(value)
        return value

    def _apply_operator(self, operator_str, field_value, value):
        """Operatörü uygular"""
        print(f"Field value: {field_value} ({type(field_value)}), Comparing with: {value} ({type(value)})")
        
        if operator_str in self.OPERATORS:
            op_func = self.OPERATORS[operator_str]
            try:
                return op_func(field_value, value)
            except Exception as e:
                print(f"Error applying operator {operator_str}: {str(e)}")
                raise ValueError(f"Error applying operator {operator_str}: {str(e)}")
        else:
            print(f"Unknown operator: {operator_str}")
            raise KeyError(f"Unknown operator: {operator_str}")

    def _get_nested_attr(self, obj, attr_path: str):
        """order.supplier.rating gibi nested attribute'ları resolve eder"""
        print(f"Resolving attribute path: {attr_path}")
        
        # Özel durumlar için kontrol
        parts = attr_path.split('.')
        current_obj = obj
        
        for i, part in enumerate(parts):
            if isinstance(current_obj, dict):
                if part in current_obj:
                    current_obj = current_obj.get(part)
                else:
                    raise KeyError(f"Key '{part}' not found in dictionary")
            else:
                # Özel durumlar için kontrol
                if i == 0 and part in obj:
                    current_obj = obj[part]
                else:
                    try:
                        current_obj = getattr(current_obj, part)
                    except AttributeError:
                        # Eğer metod ise çağır
                        if hasattr(current_obj, part) and callable(getattr(current_obj, part)):
                            current_obj = getattr(current_obj, part)()
                        else:
                            raise AttributeError(f"Attribute '{part}' not found on {current_obj}")
            
            print(f"Current object after resolving '{part}': {current_obj}")
        
        return current_obj

# Kullanım Örneği:
# context = {'order': purchase_order, 'user': request.user}
# engine = ConditionEngine(context)
# result = engine.evaluate({
#     "field": "order.toplam_tutar",
#     "operator": ">=",
#     "value": 5000
# }) 