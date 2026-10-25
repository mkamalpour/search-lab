import csv
import io
import unittest
from openpyxl import load_workbook
from ir_workbench.core import parse_documents, results_csv, xlsx_bytes, SearchIndex, demo_documents


class ImportExportTests(unittest.TestCase):
    def test_duplicate_headers_rejected_before_discarding_text(self):
        with self.assertRaisesRegex(ValueError, 'unique'):
            parse_documents('docs.csv', b'id,text,text\na,original,replacement')

    def test_spreadsheet_exports_keep_untrusted_strings_as_text(self):
        rows = [{'=heading': '=1+1', 'score': -0.25}, {'=heading': '  +cmd', 'score': 1}]
        exported = list(csv.reader(io.StringIO(results_csv(rows))))
        self.assertEqual(exported[0][0], "'=heading")
        self.assertEqual(exported[1], ["'=1+1", '-0.25'])
        book = load_workbook(io.BytesIO(xlsx_bytes(rows)))
        self.assertEqual(book.active['A2'].data_type, 's')
        self.assertEqual(book.active['B2'].value, -0.25)
        self.assertEqual(rows[0]['=heading'], '=1+1')

    def test_keywords_reject_invalid_limits(self):
        index = SearchIndex(demo_documents())
        for count in (-1, 0, True, 1.5):
            with self.subTest(count=count), self.assertRaises(ValueError):
                index.keywords('cafe', count)
