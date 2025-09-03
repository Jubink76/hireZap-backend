from abc import ABC, abstractmethod

class EmailSenderPort(ABC):
    @abstractmethod
    def send_email(self, to_email:str, subject:str, body:str):
        """ send email """
        raise NotImplementedError