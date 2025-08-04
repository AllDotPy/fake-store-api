from iswitch import (               # Use EasySwitch instead.
    Client, Transaction, AuthConfig
)

from apps.billings.models import (
    Transaction as T, RechargeTransaction as RT
)
from apps.utils.functions import (
    get_payment_credentials,
    get_default_payment_provider
)


####
##      ORDERS BUILDER 
#####
class OrderBuider:
    ''' Build Order based on Transaction service. '''
    
    def __standardize(self,transaction: RT):
        ''' Return a Payment Transaction Required fields '''
        return {
            'amount': float(transaction.amount),
            'callback_url': transaction.get_call_back_url(),
            'return_url': transaction.get_call_back_url(),
        }
        
    def build_cinetpay_order(self,transaction:RT):
        ''' Return a Cinetpay formated order from transaction '''
        
        # GET STANDARD REPRESENTATION
        data = self.__standardize(transaction)
        data |= {
            'order':{
                'currency':'XOF',
                'transaction_id': transaction.code,
                'description': f'Recharge -> {transaction.code}',
                'customer_name': transaction.user.first_name,
                'customer_surname': transaction.user.last_name,
            }
        }
        
        return data
    
    def build_semoa_order(self,transaction:RT):
        ''' Return a Semoa formated order from transaction. '''
        
        # GET STANDARD REPRESENTATION
        data = self.__standardize(transaction)
        data |= {
            'order':{
                'merchant_reference': transaction.code,
                'client': {
                    'last_name': transaction.user.last_name,
                    'first_name': transaction.user.first_name,
                    'phone': str(transaction.user.phone_number),
                }
            }
        }
        
        return data
        
    def build_transaction(self,transaction:RT,service:str=None):
        ''' Call a specific builder based on service. '''
        
        # GET PROVIDER
        provider = service or get_default_payment_provider()
        # GET BUILDER NAME
        builder = f'build_{provider.lower()}_order'
        
        # ENSURE WE HAVE THE GIVEN SERVICE BUILDER
        if hasattr(self,builder) and callable(getattr(self,builder)):
            return getattr(self,builder)(transaction)
        return None


####
##      SERVICE CLASS
#####
class PaymentService:
    ''' Payments service. '''
    
    def __init__(self):
        ''' Initialize Service. '''
        self._client = self.get_client()
        
    def get_client(self):
        ''' return a new Switch client too use. '''
        
        # INIT CLIENT WITH THE CREDENTIALS
        clnt = Client(
            configs = self.get_config()
        )
        return clnt
        
    def get_config(self):
        ''' Return the payment configuration to be used by Client. '''
        
        return AuthConfig(
            host = '',
            raise_on_error = False,
            service = get_default_payment_provider(),
            credentials = self.get_credentials()
        )
    
    def get_credentials(self):
        ''' Return Client auth credentials. '''
        return get_payment_credentials()
    
    def get_providers(self):
        ''' Return a list of supported Aggregators. '''
        
        # GET PROVIDERS
        res = self._client.list_providers()
        
        # CHECK FOR SUCCESS
        if not res.has_error:
            return res.results
        
    def get_transactions(self):
        ''' Return a list of app transactions. '''
        
        # GET TRANSACTIONS
        return self._client.list_transactions()
        
    def retrieve_transaction(self,transaction_id):
        ''' Retrieve a specific transaction by id. '''
        
        # GET TRANSACTION
        return self._client.get_transaction(
            transaction_id = transaction_id
        )
        
    def crate_transaction(self,transaction:RT):
        ''' Creates a new transaction. '''
        
        # BUILD TRANSACTION 
        order = OrderBuider().build_transaction(
            transaction = transaction
        )
        t = Transaction(**order)
        print(order)
        # SEND TRANSACTION REQUEST NOW
        return self._client.create_transaction(
            transaction = t
        )
            
# PaymentService().get_providers()