param(
    [Parameter(Mandatory = $true)]
    [string]$XmlPath,
    [string]$SchemaPath = 'c:\Users\hfjelstad\Documents\UIC NeTex Profile\XSD\xsd\NeTEx_publication.xsd',
    [int]$MaxErrors = 20
)

$errors = New-Object System.Collections.Generic.List[string]
$settings = New-Object System.Xml.XmlReaderSettings
$settings.DtdProcessing = [System.Xml.DtdProcessing]::Ignore
$settings.ValidationType = [System.Xml.ValidationType]::Schema
$settings.Schemas.Add('http://www.netex.org.uk/netex', $SchemaPath) | Out-Null
$settings.ValidationFlags = [System.Xml.Schema.XmlSchemaValidationFlags]::ProcessSchemaLocation
$settings.ValidationFlags = $settings.ValidationFlags -bor [System.Xml.Schema.XmlSchemaValidationFlags]::ReportValidationWarnings

$handler = [System.Xml.Schema.ValidationEventHandler]{
    param($sender, $e)
    $line = if ($e.Exception) { $e.Exception.LineNumber } else { 0 }
    $pos = if ($e.Exception) { $e.Exception.LinePosition } else { 0 }
    $errors.Add("$($e.Severity) line=$line pos=$pos message=$($e.Message)")
}
$settings.add_ValidationEventHandler($handler)

try {
    $reader = [System.Xml.XmlReader]::Create($XmlPath, $settings)
    while ($reader.Read()) { }
    $reader.Close()
}
catch {
    $errors.Add("Error line=0 pos=0 message=$($_.Exception.Message)")
}

$isValid = ($errors.Count -eq 0)
Write-Output "schema=$SchemaPath"
Write-Output "xml=$XmlPath"
Write-Output "valid=$isValid"
Write-Output "error_count=$($errors.Count)"

if ($errors.Count -gt 0) {
    $errors | Select-Object -First $MaxErrors | ForEach-Object {
        Write-Output '---'
        Write-Output $_
    }
    exit 1
}

exit 0
