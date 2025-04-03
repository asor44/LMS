class validator :
    def __init__(self):
        pass

    def format_datetime(dt):
        return dt.strftime("%d/%m/%Y %H:%M")

    def validate_email(email):
        import re
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return re.match(pattern, email) is not None