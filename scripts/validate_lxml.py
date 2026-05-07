"""Quick local XSD validation of all Objects/ and Frames/ XML using lxml."""
from lxml import etree
import pathlib, sys

REPO = pathlib.Path(__file__).resolve().parent.parent
xsd_path = REPO / "XSD" / "xsd" / "NeTEx_publication.xsd"

with open(xsd_path, "rb") as f:
    xmlschema = etree.XMLSchema(etree.parse(f))

errors = []
for root in ("Objects", "Frames"):
    for p in sorted((REPO / root).rglob("*.xml")):
        try:
            doc = etree.parse(str(p))
        except etree.XMLSyntaxError as e:
            errors.append(f"PARSE  {p.relative_to(REPO)}: {e}")
            continue
        if not xmlschema.validate(doc):
            for err in xmlschema.error_log:
                errors.append(f"FAIL   {p.relative_to(REPO)}:{err.line}: {err.message[:150]}")
            break  # only first error per file

if errors:
    print(f"\n{len(errors)} failure(s):")
    for e in errors:
        print(" ", e)
    sys.exit(1)
else:
    print("All XML files pass validation.")
