"""Creates XSLT object needed to transform XML to PDF."""
import logging
from lxml import etree

log = logging.getLogger(name="log." + __name__)


def transform_styl_xls_to_XLST(xsl_path: str) -> etree.XSLT:  # pylint: disable=C0103
    """
    Transforms styl.xsl file into XSLT object.

    Parameters:
        xsl_path (str): Path to styl.xsl file.

    Returns:
        xsl_transform (etree.XSLT): XSLT object.
    """
    xsl_parser = etree.XMLParser(remove_blank_text=True)
    xsl_tree = etree.parse(source=xsl_path, parser=xsl_parser)
    log.debug(msg="xsl_tree object created.")
    xsl_transform = etree.XSLT(xslt_input=xsl_tree)
    log.debug(msg="XSLT object created.")
    return xsl_transform


if __name__ == "__main__":
    transformer = transform_styl_xls_to_XLST(xsl_path="ksef_documents/styl.xsl")
    print(transformer.error_log)
