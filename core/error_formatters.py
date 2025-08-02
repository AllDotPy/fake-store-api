from drf_standardized_errors.formatter import ExceptionFormatter
from drf_standardized_errors.types import ErrorResponse


####
##      EXCEPTION FORMATTER
#####
class ExceptionFormatter(ExceptionFormatter):
    ''' Default Error formatter class. '''

    def format_error_response(self, error_response: ErrorResponse):
        ''' Error Representation. '''
        
        error = error_response.errors[0]
        # {
        #     "type": error_response.type,
        #     "code": error.code,
        #     "message": error.detail,
        #     "field_name": error.attr
        # }
        return {
            'starus': 'error',
            'message': {
                'en': f'{error.attr if error.attr else ""} {error.detail}',
                'fr': ''
            }
        }