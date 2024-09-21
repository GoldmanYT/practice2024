from datetime import datetime


class DateCheck:
    @staticmethod
    def exactMatch(text):
        try:
            _ = datetime.strptime(text, '%d.%m.%Y')
            return True
        except ValueError:
            return False
