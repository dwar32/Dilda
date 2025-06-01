import gspread
from oauth2client.service_account import ServiceAccountCredentials
import barcode
from barcode.writer import ImageWriter
import os

# Параметры
SPREADSHEET_ID = '1UQWrsdUJHkp4yOf4QKSmeKfq-a8rJs1fTpkbKY6rEM0'
SHEET_NAME = 'Лист1'
START_INDEX = 1
COUNT = 100  # Сколько товаров сгенерировать

# Генерация артикула
def generate_article(index):
    return f"DLD-{index:05d}"

# Генерация и сохранение штрихкода
def generate_ean13_barcode(number, output_path):
    EAN = barcode.get_barcode_class('ean13')
    ean = EAN(f"{number:012d}", writer=ImageWriter())
    filename = ean.save(output_path)
    return filename

# Подключение к Google Sheets
def authorize_gspread(json_keyfile_path):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile_path, scope)
    client = gspread.authorize(creds)
    return client

def main():
    # Авторизация
    client = authorize_gspread("credentials.json")  # <-- укажи свой путь к .json
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

    # Создаём папку для штрихкодов
    os.makedirs("barcodes", exist_ok=True)

    # Список строк для вставки
    rows = []

    for i in range(START_INDEX, START_INDEX + COUNT):
        article = generate_article(i)
        barcode_number = 200000000000 + i
        generate_ean13_barcode(barcode_number, f"barcodes/{article}")

        # Формируем строку: артикул, название, категория, цена, ед. изм., остатки, штрихкод
        row = [
            article, f"Товар {i}", "Категория", "0", "шт",
            "0", "0", "0", str(barcode_number), "", ""
        ]
        rows.append(row)

    # Вставляем в таблицу, начиная со 2-й строки
    sheet.update(f"A2:K{COUNT+1}", rows)

if __name__ == "__main__":
    main()
