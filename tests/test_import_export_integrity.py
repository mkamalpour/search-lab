import csv
import io
import unittest
from openpyxl import load_workbook
from ir_workbench.core import parse_documents, results_csv, xlsx_bytes, SearchIndex, demo_documents, parse_qrels


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

    def test_duplicate_qrels_headers_do_not_replace_judgments(self):
        for header, row in [
            ('query_id,doc_id,doc_id', 'q,expected,replaced'),
            ('query_id,doc_id,relevance,relevance', 'q,expected,1,0'),
            ('query_id,query_id,doc_id', 'q,other,expected'),
        ]:
            with self.subTest(header=header), self.assertRaisesRegex(ValueError, 'unique'):
                parse_qrels((header + '\n' + row).encode())
        self.assertEqual(parse_qrels(b'query_id,doc_id,relevance\nq,expected,1\nq,other,0'),
                         {'q': ['expected']})

    def test_companion_download_callbacks_escape_uploaded_formula_text(self):
        import hashlib
        from types import SimpleNamespace
        from unittest.mock import MagicMock, patch
        import pandas as pd
        import numpy as np
        from ir_workbench.companion_core import SCORES
        from ir_workbench.companion_ui import _lab

        frame = pd.DataFrame({'full_text': ['=1+1'], **{c: [2] for c in SCORES}})
        upload = io.BytesIO(frame.to_csv(index=False).encode())
        batch = io.BytesIO(b'full_text\n+SUM(1)\n')
        model = SimpleNamespace(
            vectorizer=SimpleNamespace(vocabulary_={}, get_feature_names_out=lambda: np.array([])),
            predict=lambda data: np.full((len(data), 6), 2.),
        )
        fake = MagicMock()
        fake.session_state = {
            'companion_essay': (model, {}, frame.copy()),
            'companion_essay_fingerprint': hashlib.sha256(frame.to_json().encode()).hexdigest(),
        }
        fake.file_uploader.side_effect = [upload, batch]
        fake.checkbox.return_value = False
        fake.button.return_value = False
        fake.text_area.return_value = ''
        with patch('ir_workbench.companion_ui.st', fake):
            _lab('essay')
        downloads = {call.args[0]: call.args[1] for call in fake.download_button.call_args_list}
        validation = list(csv.DictReader(io.StringIO(downloads['Download validation predictions'])))
        prediction = list(csv.DictReader(io.StringIO(downloads['Download batch predictions'])))
        self.assertEqual(validation[0]['full_text'], "'=1+1")
        self.assertEqual(validation[0]['cohesion'], '2')
        self.assertEqual(prediction[0]['full_text'], "'+SUM(1)")
        self.assertEqual(frame.full_text.tolist(), ['=1+1'])
