import csv
import tempfile

from loguru import logger


def validate_column_headers_csv(csv_row, header, exception_type):
    for (label, column) in header.items():
        cell_value = csv_row[column].strip()
        if (label != 'Pixels' and label != cell_value) or (label == 'Pixels' and cell_value != ''):
            raise CsvException("{exception} exception. column: {col}, expected: '{expected}', actual: '{actual}'".format(
                exception=exception_type, col=column, expected=label, actual=cell_value
            ))


def write_csv_temp_file(field_names:list[str], data:dict) -> str:
    file_name = None
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
        file_name = temp_file.name

    write_csv_file(fie, data, file_name)
    return file_name


def write_csv_file(field_names:list[str], data:dict, file_name:str):
    with open(file_name, 'w', newline='') as f:
        csv_writer = csv.DictWriter(f, field_names)
        csv_writer.writeheader()

        for key in data.keys():
            csv_writer.writerow(data[key])


def load_csv(csv_file_path, with_header_row=True, delimiter=','):
    logger.info("loading csv file '{}' ...".format(csv_file_path))

    data = {}

    with open(csv_file_path, newline='') as fil:
        line = 1
        header = None

        for row in csv.reader(fil, delimiter=delimiter):
            if line == 1:
                if with_header_row:
                    header = _header_from_csv_row(row)
                else:
                    logger.error('support for "with_header_row=False" not implemented yet')

            else:
                row_data = _extract_row_data_csv(header, row)
                row_key = "row:{}".format(line)
                data[row_key] = row_data

            line += 1

    return data


def _header_from_csv_row(row):
    header = {}

    for i in range(len(row)):
        header[row[i]] = i
    
    return header


def _extract_row_data_csv(header, row):
    row_data = {}

    for (attribute, column) in header.items():
        row_data[attribute] = row[column]

    return row_data


class CsvException(Exception):

    def __init__(self, message):
        self.err = message
        super().__init__(self.err)
