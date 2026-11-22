
import pythoncom
import win32com.client

print("Проверка COM-интерфейса OpenServer")

try:
    server = win32com.client.Dispatch("PX32.OpenServer.1")
    print("УСПЕХ: COM-объект OpenServer найден")

except pythoncom.com_error as error:
    print("ОШИБКА COM")
    print("HRESULT:", error.hresult)
    print("Описание:", error.strerror)
    print("Подробности:", error.excepinfo)

except Exception as error:
    print("Тип ошибки:", type(error).__name__)
    print("Причина:", str(error))
