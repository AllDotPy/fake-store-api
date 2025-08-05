# Custom Exceptions Guide

## Usage Rules

### 1. Use model-specific exceptions

✅ **Good:**
```python
raise UserNotFoundError(details="User not found")
raise NotificationNotFoundError(details="Notification not found")
```

❌ **Avoid:**
```python
raise DataNotFoundError(details="User not found")  # Too generic
```

### 2. Clear and informative messages

✅ **Good:**
```python
raise UserAuthenticationError(
    details="Invalid credentials. Please check your email/password."
)
```

### 3. Migration from Response

**Before:**
```python
return Response({'detail': 'Error'}, status=404)
```

**After:**
```python
raise UserNotFoundError(details="User not found")
```

## Exceptions by Model

- **Users** : `UserNotFoundError`, `UserAuthenticationError`
- **Products** : `ProductNotFoundError`, `ProductOutOfStockError`
- **Orders** : `OrderNotFoundError`, `OrderValidationError`
- **Categories** : `CategoryNotFoundError`
- **Notifications** : `NotificationNotFoundError`, `NotificationServiceError`
- **Payments** : `PaymentError`, `InsufficientFundsError` 