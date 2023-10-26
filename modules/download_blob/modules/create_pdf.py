"""converts xml to pdf"""
import logging
import io

from lxml import etree
from pdfdocument.document import PDFDocument


log = logging.getLogger(name="log." + __name__)


def main(xml_bytes: bytes, xslt_transformer: etree.XSLT) -> bytes:
    # Parse the XML input.
    xml_parser = etree.XMLParser(remove_blank_text=True)
    xml_tree = etree.parse(
        source=io.BytesIO(initial_bytes=xml_bytes), parser=xml_parser
    )
    log.debug(msg=f"XML tree created: {xml_tree}.")

    # Transform the XML input into an XSL-FO tree.
    try:
        fo_tree = xslt_transformer(xml_tree)  # results in etree.XSLTApplyError
        # XSLTApplyError('Cannot resolve URI http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/KodyKrajow_v10-0E.xsd')
    except etree.XSLTApplyError as exc:
        log.error(msg=f"XSLTApplyError: {exc}.")
        raise exc
    log.debug(msg=f"XSL-FO tree created: {fo_tree}.")

    # Generate the PDF output from the XSL-FO tree.
    pdf_bytes = io.BytesIO()
    pdf_doc = PDFDocument(pdf_bytes)
    pdf_doc.init_report()
    pdf_doc.add_raw_data(fo_tree.tostring())
    pdf_doc.generate()

    return pdf_bytes.getvalue()
