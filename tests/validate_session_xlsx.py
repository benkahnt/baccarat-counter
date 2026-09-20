#!/usr/bin/env python3
"""Validate the native Sessionverlauf.xlsx package without third-party modules."""
from __future__ import annotations

import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {
    "x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/package/2006/relationships",
    "ct": "http://schemas.openxmlformats.org/package/2006/content-types",
}


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        ".validation/out/BaccaratCounter/Sessionverlauf.xlsx"
    )
    if not path.is_file():
        raise SystemExit(f"XLSX not found: {path}")

    required = {
        "[Content_Types].xml",
        "_rels/.rels",
        "xl/workbook.xml",
        "xl/_rels/workbook.xml.rels",
        "xl/styles.xml",
        "xl/worksheets/sheet1.xml",
    }

    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        missing = required - names
        assert not missing, f"missing package parts: {sorted(missing)}"
        assert zf.testzip() is None, "ZIP CRC/integrity failure"
        for info in zf.infolist():
            assert info.date_time >= (1980, 1, 1, 0, 0, 0), (
                f"invalid DOS ZIP timestamp for {info.filename}: {info.date_time}"
            )

        parsed = {}
        for name in required:
            if name.endswith(".xml") or name.endswith(".rels"):
                parsed[name] = ET.fromstring(zf.read(name))

        sheet = parsed["xl/worksheets/sheet1.xml"]
        children = [local(child.tag) for child in sheet]
        expected_order = [
            "dimension", "sheetViews", "sheetFormatPr", "cols",
            "sheetData", "autoFilter", "pageMargins",
        ]
        positions = {name: children.index(name) for name in expected_order}
        assert positions == dict(sorted(positions.items(), key=lambda kv: expected_order.index(kv[0])))
        assert [positions[n] for n in expected_order] == sorted(positions.values()), (
            f"worksheet child order invalid: {children}"
        )

        dimension = sheet.find("x:dimension", NS)
        assert dimension is not None and dimension.attrib.get("ref", "").startswith("A1:AA")
        sheet_data = sheet.find("x:sheetData", NS)
        assert sheet_data is not None and sheet_data.find("x:row", NS) is not None
        auto_filter = sheet.find("x:autoFilter", NS)
        assert auto_filter is not None and auto_filter.attrib.get("ref", "").startswith("A4:AA")

        wb = parsed["xl/workbook.xml"]
        sheet_node = wb.find("x:sheets/x:sheet", NS)
        assert sheet_node is not None and sheet_node.attrib.get("name") == "Sessions"

        rels = parsed["xl/_rels/workbook.xml.rels"]
        targets = {r.attrib.get("Target") for r in rels}
        assert "worksheets/sheet1.xml" in targets
        assert "styles.xml" in targets

        types = parsed["[Content_Types].xml"]
        overrides = {o.attrib.get("PartName") for o in types.findall("ct:Override", NS)}
        assert "/xl/workbook.xml" in overrides
        assert "/xl/worksheets/sheet1.xml" in overrides
        assert "/xl/styles.xml" in overrides

    # v110: new policy values, percentages and matched-coverage delta.
    def cells(book):
        with zipfile.ZipFile(book) as z:
            root = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
            return {c.attrib['r']: c for c in root.findall('.//x:c', NS)}

    data = cells(path.parent / 'coverage.xlsx')
    def value(ref):
        return float(data[ref].find('x:v', NS).text)
    assert value('R5') == 14.75 and value('S5') == 6.5 and value('T5') == 7
    assert data['S5'].find('x:f', NS).text == 'R5-K5'
    assert value('U5') == .0025 and value('V5') == .0025
    assert data['U5'].attrib['s'] == '6'
    assert all(f'{col}6' not in data for col in 'RSTUV'), 'old history must stay blank'
    assert value('R7') == 0 and value('T7') == 0 and value('U7') == 0
    assert value('V7') == .0225
    assert value('L2') == 14.75 and value('N2') == 6.5 and value('P2') == 2
    assert data['N2'].find('x:f', NS).text == 'SUM(S5:S7)'
    assert data['P7'].find('x:is/x:t', NS).text == 'AUS'
    old = cells(path.parent / 'legacy-only.xlsx')
    assert 'L2' not in old and 'N2' not in old, 'no new history is unavailable, not zero'
    assert old['J2'].find('x:v', NS).text == 'Kein vollständiger Vergleich'
    data = cells(path.parent / 'three-models.xlsx')
    assert value('R2') == 2
    assert value('T2') == -76.75 and value('V2') == -77.75 and value('X2') == -66.75
    assert data['J2'].find('x:v', NS).text == 'Gesamt-MinEdge (0,25 %)'
    assert data['J2'].attrib['t'] == 'str'
    assert 'MAX(T2,V2,X2)' in data['J2'].find('x:f', NS).text
    assert 'ISNUMBER(R5:R7)' in data['T2'].find('x:f', NS).text
    assert data['Z2'].find('x:is/x:t', NS).text == '0,25 %'

    print(f"Session XLSX package OK: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
