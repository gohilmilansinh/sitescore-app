import os
import tempfile

from report import generate_report


def test_generate_report_creates_pdf():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "site_report.pdf")
        result = {
            "scores": {
                "demand": 80,
                "footfall": 60,
                "competition": 70,
                "accessibility": 55,
                "catchment": 40,
                "spending_power": 50,
            },
            "total_score": 65,
        }

        generate_report(result, output_path=output_path)
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
