# -*- coding: utf-8 -*-
"""
Tests of Internal BoM files

- Simple cases for:
  - CSV
  - HTML
  - XML
  - XLSX
- Components units
  - Sort and groups of RLC_sort
- Datasheet as link
- Digi-Key link
- Join columns
- ignore_dnf = 0
- html_generate_dnf = 0
- use_alt = 1 (also non contiguous)
- COLUMN_RENAME
  - CSV
  - HTML
  - XML
  - XLSX
- group_connectors = 1/0
- Columns are case insensitive
- component_aliases
- merge_blank_fields
- Don't group components
- Multipart component (not repeated)
- Field collision
- test_regex/exclude_any/include_only

Missing:
- Variants
- number_boards
- hide_headers
- hide_pcb_info
- various boards
- stats info
- datasheet and digikey for XLSX

- XLSX colors

For debug information use:
pytest-3 --log-cli-level debug

"""

import os
import sys
import logging
# Look for the 'utils' module from where the script is running
prev_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
# Utils import
from utils import context
prev_dir = os.path.dirname(prev_dir)
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
# from kiplot.misc import (BOM_ERROR)

BOM_DIR = 'BoM'
REF_COLUMN_NAME = 'References'
REF_COLUMN_NAME_R = 'Referencias'
QTY_COLUMN_NAME = 'Quantity Per PCB'
COMP_COLUMN_NAME = 'Row'
COMP_COLUMN_NAME_R = 'Renglón'
KIBOM_TEST_HEAD = [COMP_COLUMN_NAME, 'Description', 'Part', REF_COLUMN_NAME, 'Value', 'Footprint', QTY_COLUMN_NAME,
                   'Datasheet', 'Config']
KIBOM_TEST_HEAD_TOL = [c for c in KIBOM_TEST_HEAD]
KIBOM_TEST_HEAD_TOL.insert(-1, 'Tolerance')
KIBOM_RENAME_HEAD = [COMP_COLUMN_NAME_R, REF_COLUMN_NAME_R, 'Componente', 'Valor', 'Código Digi-Key', 'Cantidad por PCB']
CONN_HEAD = [COMP_COLUMN_NAME, 'Description', 'Part', REF_COLUMN_NAME, 'Value', 'Footprint', QTY_COLUMN_NAME, 'Datasheet']
KIBOM_TEST_COMPONENTS = ['C1', 'C2', 'C3', 'C4', 'R1', 'R2', 'R3', 'R4', 'R5', 'R7', 'R8', 'R9', 'R10']
KIBOM_TEST_COMPONENTS_ALT = ['C1-C4', 'R9-R10', 'R7', 'R8', 'R1-R5']
KIBOM_TEST_COMPONENTS_ALT2 = ['C1-C4', 'R9-R10', 'R7', 'R8', 'R1-R2', 'R4-R5', 'R3']
KIBOM_TEST_EXCLUDE = ['R6']
KIBOM_TEST_GROUPS = 5
LINKS_COMPONENTS = ['J1', 'J2', 'R1']
LINKS_EXCLUDE = ['C1']
LINKS_GROUPS = 2
INFO_ROWS = ['Schematic:', 'Variant:', 'Revision:', 'Date:', 'KiCad Version:']
STATS_ROWS = ['Component Groups:', 'Component Count:', 'Fitted Components:', 'Number of PCBs:', 'Total components:']


def check_kibom_test_netlist(rows, ref_column, groups, exclude, comps):
    """ Checks the kibom-test.sch expected results """
    # Groups
    assert len(rows) == groups
    logging.debug(str(groups) + " groups OK")
    # Components
    if comps:
        components = []
        for r in rows:
            components.extend(r[ref_column].split(' '))
        assert len(components) == len(comps)
        logging.debug(str(len(comps)) + " components OK")
    # Excluded
    if exclude:
        for ex in exclude:
            assert ex not in components
        logging.debug(str(len(exclude)) + " not fitted OK")
    # All the other components
    if comps:
        for c in comps:
            assert c in components
        logging.debug("list of components OK")


def check_dnc(rows, comp, ref, qty):
    for row in rows:
        if row[ref].find(comp) != -1:
            assert row[qty] == '1 (DNC)'
            logging.debug(comp + " is DNC OK")
            return


def check_path(rows, comp, ref, sp, val):
    for row in rows:
        if row[ref].find(comp) != -1:
            assert row[sp] == val
            logging.debug(comp + " sheetpath OK")
            return


def check_head_xlsx(r, info, stats, title='KiBot Bill of Materials'):
    rn = 0
    if title:
        # First row is just the title
        assert r[rn][0] == title
        rn += 1
        logging.debug('Title Ok')
    if info:
        info_col = 0
        for i, txt in enumerate(info):
            assert r[rn+i][info_col] == INFO_ROWS[i]
            if txt:
                assert r[rn+i][info_col+1] == txt
        logging.debug('Info block Ok')
    if stats:
        stats_col = 0
        if info:
            stats_col += 2
        for i, txt in enumerate(stats):
            assert r[rn+i][stats_col] == STATS_ROWS[i]
            assert r[rn+i][stats_col+1] == txt, 'index: {} title: {}'.format(i, STATS_ROWS[i])
        logging.debug('Stats block Ok')


def test_int_bom_simple_csv():
    prj = 'kibom-test'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_simple_csv', prj, 'int_bom_simple_csv', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_simple_html():
    prj = 'kibom-test'
    ext = 'html'
    ctx = context.TestContextSCH('test_int_bom_simple_html', prj, 'int_bom_simple_html', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, headers = ctx.load_html(out)
    # Test we got the normal and DNF tables
    assert len(rows) == 2
    assert len(headers) == 2
    # Test both tables has the same headings and they are the expected
    assert headers[0] == headers[1]
    assert headers[0] == KIBOM_TEST_HEAD
    # Look for reference and quantity columns
    ref_column = headers[0].index(REF_COLUMN_NAME)
    qty_column = headers[0].index(QTY_COLUMN_NAME)
    # Check the normal table
    check_kibom_test_netlist(rows[0], ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows[0], 'R7', ref_column, qty_column)
    # Check the DNF table
    check_kibom_test_netlist(rows[1], ref_column, 1, KIBOM_TEST_COMPONENTS, KIBOM_TEST_EXCLUDE)
    ctx.clean_up()


def adapt_xml(h):
    h = h.replace(' ', '_')
    h = h.replace('"', '')
    h = h.replace("'", '')
    h = h.replace('#', '_num')
    return h


def test_int_bom_simple_xml():
    prj = 'kibom-test'
    ext = 'xml'
    ctx = context.TestContextSCH('test_int_bom_simple_xml', prj, 'int_bom_simple_xml', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header = ctx.load_xml(out)
    # Columns get sorted by name, so we need to take care of it
    for c in KIBOM_TEST_HEAD:
        assert adapt_xml(c) in header, "Missing column "+c
    ref_column = header.index(adapt_xml(REF_COLUMN_NAME))
    qty_column = header.index(adapt_xml(QTY_COLUMN_NAME))
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def simple_xlsx_verify(ctx, prj):
    ext = 'xlsx'
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, sh_head = ctx.load_xlsx(out)
    check_head_xlsx(sh_head,
                    [prj, 'default', 'A', '2020-03-12', None],
                    [KIBOM_TEST_GROUPS+len(KIBOM_TEST_EXCLUDE),
                     len(KIBOM_TEST_COMPONENTS)+len(KIBOM_TEST_EXCLUDE),
                     len(KIBOM_TEST_COMPONENTS),
                     1,
                     len(KIBOM_TEST_COMPONENTS)])
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_simple_xlsx():
    prj = 'kibom-test'
    ctx = context.TestContextSCH('test_int_bom_simple_xlsx', prj, 'int_bom_simple_xlsx', BOM_DIR)
    simple_xlsx_verify(ctx, prj)


def get_column(rows, col, split=True):
    components = []
    for r in rows:
        if split:
            components.extend(r[col].split())
        else:
            components.append(r[col])
    return components


def test_int_bom_sort_1():
    prj = 'RLC_sort'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_sort_1', prj, 'int_bom_simple_csv', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header = ctx.load_csv(out)
    ref_column = header.index(REF_COLUMN_NAME)
    exp = ['C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C1', 'C2', 'C3', 'C4', 'C11', 'C12',
           'R5', 'R4', 'R9', 'R10', 'R3', 'R2', 'R1', 'R8', 'R7']
    check_kibom_test_netlist(rows, ref_column, 14, None, exp)
    # Check the sorting
    assert get_column(rows, ref_column) == exp
    ctx.clean_up()


def test_int_bom_datasheet_link():
    prj = 'links'
    ext = 'html'
    ctx = context.TestContextSCH('test_int_bom_datasheet_link', prj, 'int_bom_datasheet_link', BOM_DIR)
    ctx.run()
    out = prj + '.' + ext
    rows, headers = ctx.load_html(out)
    # Test we got the normal and DNF tables
    assert len(rows) == 2
    assert len(headers) == 2
    # Test both tables has the same headings and they are the expected
    assert headers[0] == headers[1]
    assert headers[0] == ['References', 'Part', 'Value', 'Quantity Per PCB', 'digikey#', 'manf#']
    # Look for reference and quantity columns
    ref_column = headers[0].index(REF_COLUMN_NAME)
    part_column = headers[0].index('Part')
    # Check the normal table
    check_kibom_test_netlist(rows[0], ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    # Check the DNF table
    check_kibom_test_netlist(rows[1], ref_column, 1, LINKS_COMPONENTS, LINKS_EXCLUDE)
    # Check the datasheet link
    parts = get_column(rows[0]+rows[1], part_column, False)
    for c in parts:
        assert c.strip().startswith('<a href')
        assert 'pdf' in c
        logging.debug(c + ' OK')
    ctx.clean_up()


def test_int_bom_digikey_link():
    prj = 'links'
    ext = 'html'
    ctx = context.TestContextSCH('test_int_bom_digikey_link', prj, 'int_bom_digikey_link', BOM_DIR)
    ctx.run()
    out = prj + '.' + ext
    rows, headers = ctx.load_html(out)
    # Test we got the normal and DNF tables
    assert len(rows) == 2
    assert len(headers) == 2
    # Test both tables has the same headings and they are the expected
    assert headers[0] == headers[1]
    assert headers[0] == ['References', 'Part', 'Value', 'Quantity Per PCB', 'digikey#', 'manf#']
    # Look for reference and quantity columns
    ref_column = headers[0].index(REF_COLUMN_NAME)
    dk_column = headers[0].index('digikey#')
    # Check the normal table
    check_kibom_test_netlist(rows[0], ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    # Check the DNF table
    check_kibom_test_netlist(rows[1], ref_column, 1, LINKS_COMPONENTS, LINKS_EXCLUDE)
    # Check the digikey link
    parts = get_column(rows[0]+rows[1], dk_column, False)
    for c in parts:
        assert c.strip().startswith('<a href')
        assert 'digikey' in c
        logging.debug(c + ' OK')
    ctx.clean_up()


def test_int_bom_join_1():
    prj = 'join'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_join_1', prj, 'int_bom_join_1', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header = ctx.load_csv(out)
    assert header == [COMP_COLUMN_NAME, REF_COLUMN_NAME, 'Part', 'Value', 'manf', 'digikey#', QTY_COLUMN_NAME]
    ref_column = header.index(REF_COLUMN_NAME)
    manf_column = header.index('manf')
    value_column = header.index('Value')
    check_kibom_test_netlist(rows, ref_column, LINKS_GROUPS+1, [], LINKS_EXCLUDE+LINKS_COMPONENTS)
    assert rows[0][ref_column] == 'C1'
    assert rows[0][value_column] == '1nF 10% 50V'
    assert rows[0][manf_column] == 'KEMET C0805C102K5RACTU'
    assert rows[1][ref_column] == 'J1 J2'
    assert rows[1][value_column] == 'Molex KK'
    assert rows[1][manf_column] == 'Molex 0022232021'
    assert rows[2][ref_column] == 'R1'
    assert rows[2][value_column] == '1k 5%'
    assert rows[2][manf_column] == 'Bourns CR0805-JW-102ELF'
    ctx.clean_up()


def test_int_include_dnf():
    """ ignore_dnf: false """
    prj = 'kibom-test'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_include_dnf', prj, 'int_bom_include_dnf', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS+1, [], KIBOM_TEST_COMPONENTS+KIBOM_TEST_EXCLUDE)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_html_generate_dnf():
    """ html_generate_dnf: false """
    prj = 'kibom-test'
    ext = 'html'
    ctx = context.TestContextSCH('test_int_bom_html_generate_dnf', prj, 'int_bom_html_generate_dnf', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, headers = ctx.load_html(out)
    logging.debug(rows)
    # Test we got the normal and DNF tables
    assert len(rows) == 1
    assert len(headers) == 1
    assert headers[0] == KIBOM_TEST_HEAD
    # Look for reference and quantity columns
    ref_column = headers[0].index(REF_COLUMN_NAME)
    qty_column = headers[0].index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows[0], ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows[0], 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_use_alt():
    """ use_alt: true """
    prj = 'kibom-test'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_use_alt', prj, 'int_bom_use_alt', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS_ALT)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_use_alt_2():
    """ use_alt: true and not merge blank fields, non contiguous """
    prj = 'kibom-test-2'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_use_alt_2', prj, 'int_bom_use_alt_2', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    # R3 without footprint won't be merged with other 10K resistors
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS+1, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS_ALT2)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_no_number_rows():
    """ Was number_rows: false, now is different """
    prj = 'kibom-test'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_no_number_rows', prj, 'int_bom_no_number_rows', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD[1:]
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_column_rename_csv():
    prj = 'links'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_column_rename_csv', prj, 'int_bom_column_rename_csv', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header = ctx.load_csv(out)
    assert header == KIBOM_RENAME_HEAD
    ref_column = header.index(REF_COLUMN_NAME_R)
    check_kibom_test_netlist(rows, ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    ctx.clean_up()


def test_int_bom_column_rename_html():
    prj = 'links'
    ext = 'html'
    ctx = context.TestContextSCH('test_int_bom_column_rename_html', prj, 'int_bom_column_rename_html', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, headers = ctx.load_html(out)
    assert headers[0] == KIBOM_RENAME_HEAD
    ref_column = headers[0].index(REF_COLUMN_NAME_R)
    check_kibom_test_netlist(rows[0], ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    ctx.clean_up()


def test_int_bom_column_rename_xml():
    prj = 'links'
    ext = 'xml'
    ctx = context.TestContextSCH('test_int_bom_column_rename_xml', prj, 'int_bom_column_rename_xml', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header = ctx.load_xml(out)
    # Columns get sorted by name, so we need to take care of it
    for c in KIBOM_RENAME_HEAD:
        assert adapt_xml(c) in header, "Missing column "+c
    ref_column = header.index(REF_COLUMN_NAME_R)
    check_kibom_test_netlist(rows, ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    ctx.clean_up()


def test_int_bom_column_rename_xlsx():
    prj = 'links'
    ext = 'xlsx'
    ctx = context.TestContextSCH('test_int_bom_column_rename_xlsx', prj, 'int_bom_column_rename_xlsx', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, sh_head = ctx.load_xlsx(out)
    assert header == KIBOM_RENAME_HEAD
    ref_column = header.index(REF_COLUMN_NAME_R)
    check_kibom_test_netlist(rows, ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    ctx.clean_up()


def test_int_bom_group_connectors():
    """ Default behavior, ignore the 'Value' for connectors """
    prj = 'connectors'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_group_connectors', prj, 'int_bom_simple_csv', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header = ctx.load_csv(out)
    assert header == CONN_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 2, [], ['J4', 'J1', 'J3', 'J2'])
    ctx.clean_up()


def test_int_bom_no_group_connectors():
    """ group_connectors: false """
    prj = 'connectors'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_no_group_connectors', prj, 'int_bom_no_group_connectors', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header = ctx.load_csv(out)
    assert header == CONN_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 4, [], ['J4', 'J1', 'J3', 'J2'])
    ctx.clean_up()


def test_int_bom_column_sensitive():
    """ Test if the columns list can contain columns in lowercase """
    prj = 'links'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_column_sensitive', prj, 'int_bom_column_sensitive', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header = ctx.load_csv(out)
    assert header == [REF_COLUMN_NAME.lower(), 'value', 'part', 'description']
    ref_column = header.index(REF_COLUMN_NAME.lower())
    check_kibom_test_netlist(rows, ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    ctx.clean_up()


def test_int_bom_alias_csv():
    """ Component aliases and merge blank fields """
    prj = 'kibom-test-2'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_alias_csv', prj, 'int_bom_alias_csv', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_alias_nm_csv():
    """ Component aliases and not merge blank fields """
    prj = 'kibom-test-2'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_alias_nm_csv', prj, 'int_bom_alias_nm_csv', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    # R3 without footprint won't be merged with other 10K resistors
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS+1, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_no_group_csv():
    """ Don't group components """
    prj = 'kibom-test'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_no_group_csv', prj, 'int_bom_no_group_csv', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    # R3 without footprint won't be merged with other 10K resistors
    check_kibom_test_netlist(rows, ref_column, len(KIBOM_TEST_COMPONENTS), KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_repeat_csv():
    """ Multipart component (not repeated)
        Also DNC in value + Config. """
    prj = 'kibom-test-rep'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_repeat_csv', prj, 'int_bom_simple_csv', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 2, ['R2'], ['U1', 'R1'])
    check_dnc(rows, 'R1', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_collision():
    """ Field collision and exclude_any """
    prj = 'kibom-test-3'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_collision', prj, 'int_bom_simple_csv', BOM_DIR)
    ctx.run(extra_debug=True)
    out = prj + '-bom.' + ext
    rows, header = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD_TOL
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.search_err('Field conflict')
    ctx.clean_up()


def test_int_bom_include_only():
    """ Include only (0805 components) """
    prj = 'kibom-test'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_include_only', prj, 'int_bom_include_only', BOM_DIR)
    ctx.run(extra_debug=True)
    out = prj + '-bom.' + ext
    rows, header = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 3, KIBOM_TEST_EXCLUDE, ['R1', 'R2', 'R3', 'R4', 'R5', 'R7', 'R8'])
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_no_test_regex():
    prj = 'kibom-test'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_simple_csv', prj, 'int_bom_no_include_only', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_sub_sheet_alt():
    """ Test for 1 sub sheet used twice.
        Also stress the v5 loader.
        Also tests sheet path and no grouping with multi-part components """
    prj = 'test_v5'
    ext = 'csv'
    ctx = context.TestContextSCH('test_int_bom_sub_sheet_alt', prj, 'int_bom_sheet_path', BOM_DIR)
    ctx.run()  # extra_debug=True
    out = prj + '-bom.' + ext
    rows, header = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD[:-1] + ['Sheetpath']
    ref_column = header.index(REF_COLUMN_NAME)
    sp_column = header.index('Sheetpath')
    check_kibom_test_netlist(rows, ref_column, 6, [], ['C1', 'L1', 'R1', 'R2', 'U1', 'U2'])
    check_path(rows, 'U1', ref_column, sp_column, '/Sub Sheet')
    check_path(rows, 'U2', ref_column, sp_column, '/Sub Sheet 2')
    ctx.clean_up()


def test_int_bom_simple_xlsx_2():
    """ No title """
    prj = 'kibom-test'
    ext = 'xlsx'
    ctx = context.TestContextSCH('test_int_bom_simple_xlsx_2', prj, 'int_bom_simple_xlsx_2', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, sh_head = ctx.load_xlsx(out)
    check_head_xlsx(sh_head,
                    [prj, 'default', 'A', '2020-03-12', None],
                    [KIBOM_TEST_GROUPS+len(KIBOM_TEST_EXCLUDE),
                     len(KIBOM_TEST_COMPONENTS)+len(KIBOM_TEST_EXCLUDE),
                     len(KIBOM_TEST_COMPONENTS),
                     1,
                     len(KIBOM_TEST_COMPONENTS)],
                    title=None)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_simple_xlsx_3():
    """ No logo """
    prj = 'kibom-test'
    ctx = context.TestContextSCH('test_int_bom_simple_xlsx_3', prj, 'int_bom_simple_xlsx_3', BOM_DIR)
    simple_xlsx_verify(ctx, prj)


def test_int_bom_simple_xlsx_4():
    """ No title, no logo """
    prj = 'kibom-test'
    ext = 'xlsx'
    ctx = context.TestContextSCH('test_int_bom_simple_xlsx_4', prj, 'int_bom_simple_xlsx_4', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, sh_head = ctx.load_xlsx(out)
    check_head_xlsx(sh_head,
                    [prj, 'default', 'A', '2020-03-12', None],
                    [KIBOM_TEST_GROUPS+len(KIBOM_TEST_EXCLUDE),
                     len(KIBOM_TEST_COMPONENTS)+len(KIBOM_TEST_EXCLUDE),
                     len(KIBOM_TEST_COMPONENTS),
                     1,
                     len(KIBOM_TEST_COMPONENTS)],
                    title=None)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_simple_xlsx_5():
    """ No title, no logo, no info """
    prj = 'kibom-test'
    ext = 'xlsx'
    ctx = context.TestContextSCH('test_int_bom_simple_xlsx_5', prj, 'int_bom_simple_xlsx_5', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, sh_head = ctx.load_xlsx(out)
    check_head_xlsx(sh_head,
                    None,
                    [KIBOM_TEST_GROUPS+len(KIBOM_TEST_EXCLUDE),
                     len(KIBOM_TEST_COMPONENTS)+len(KIBOM_TEST_EXCLUDE),
                     len(KIBOM_TEST_COMPONENTS),
                     1,
                     len(KIBOM_TEST_COMPONENTS)],
                    title=None)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_simple_xlsx_6():
    """ No title, no logo, no info, no stats """
    prj = 'kibom-test'
    ext = 'xlsx'
    ctx = context.TestContextSCH('test_int_bom_simple_xlsx_6', prj, 'int_bom_simple_xlsx_6', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, sh_head = ctx.load_xlsx(out)
    assert len(sh_head) == 0
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    qty_column = header.index(QTY_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, qty_column)
    ctx.clean_up()


def test_int_bom_simple_xlsx_7():
    """ Logo from file, no colors (no real test for the style) """
    prj = 'kibom-test'
    ctx = context.TestContextSCH('test_int_bom_simple_xlsx_7', prj, 'int_bom_simple_xlsx_7', BOM_DIR)
    simple_xlsx_verify(ctx, prj)


def test_int_bom_simple_xlsx_8():
    """ Style green (no real test for the style) """
    prj = 'kibom-test'
    ctx = context.TestContextSCH('test_int_bom_simple_xlsx_8', prj, 'int_bom_simple_xlsx_8', BOM_DIR)
    simple_xlsx_verify(ctx, prj)


def test_int_bom_simple_xlsx_9():
    """ Style red (no real test for the style) """
    prj = 'kibom-test'
    ctx = context.TestContextSCH('test_int_bom_simple_xlsx_9', prj, 'int_bom_simple_xlsx_9', BOM_DIR)
    simple_xlsx_verify(ctx, prj)
