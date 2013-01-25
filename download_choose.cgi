#!/usr/bin/perl

use CGI;

use lib ('./lib/');
use Glossa_local;

print "Content-type: text/html\n\n";

my $corpus = CGI::param('corpus');

my %conf = Glossa::readConfig($corpus);

my $dsn = "DBI:mysql:database=$conf{'db_name'};host=$conf{'db_host'}";
$dbh = DBI->connect($dsn, $conf{'db_uname'}, $conf{'db_pwd'}, {RaiseError => 0}) || die $DBI::errstr;

my $query_id = CGI::param('query_id');

print "<html><head></head><body>";
my $speech = 0;
if($conf{'corpus_mode'} eq 'speech'){$speech = 1;}

print "<form action=\"", $conf{'cgiRoot'}, "/download.cgi\" method=\"get\">";
print "<input type=\"hidden\" name=\"query_id\" value=\"$query_id\">";
print "<input type=\"hidden\" name=\"corpus\" value=\"$corpus\">";

print "<input type=\"checkbox\" name=\"head\" checked></input> Create headings<br>";

print "<table cellspacing=\"10\"><tr><td valign=\"top\">";

print "<b>Token data (all):</b><br>";
print "<input type=\"checkbox\" name=\"form\" checked></input> Orthographic<br>";
print "<input type=\"checkbox\" name=\"lexeme\"></input> Lexeme<br>";
print "<input type=\"checkbox\" name=\"pos\"></input> POS tag<br>";
if($speech){
    print "<input type=\"checkbox\" name=\"phon\"></input> Phonetic <br>";
}

print "<b>Token data (match):</b><br>";
print "<input type=\"checkbox\" name=\"mform\" checked></input> Orthographic<br>";
print "<input type=\"checkbox\" name=\"mlexeme\"></input> Lexeme<br>";
print "<input type=\"checkbox\" name=\"mpos\"></input> POS tag<br>";
if($speech){
    print "<input type=\"checkbox\" name=\"mphon\"></input> Phonetic <br>";
}

print "</td><td valign=\"top\">";

print "<b>Metadata:</b><br>";
print "<input type=\"checkbox\" name=\"text_id\"></input> Text id<br>";
print "<input type=\"checkbox\" name=\"sent_id\" checked></input> Sentence id<br>";
print "<input type=\"checkbox\" name=\"author\"></input> Author<br>";
print "<input type=\"checkbox\" name=\"language\"></input> Language<br>";
print "<input type=\"checkbox\" name=\"date\"></input> Publication date<br>";

if ($conf{'type'} eq 'multilingual') {
    print "</tr><tr><td valign=\"top\">";
    print "<b><font size=\"+1\"><I>Alignments:</I></font></b><br>";
    print "<input type=\"checkbox\" name=\"align\" checked></input> Include aligmnents";
    
    print "</tr><tr><td valign=\"top\">";
    print "<b>Token data (aligment):</b><br>";
    print "<input type=\"checkbox\" name=\"aform\" checked></input> Orthographic<br>";
    print "<input type=\"checkbox\" name=\"alexeme\"></input> Lexeme<br>";
    print "<input type=\"checkbox\" name=\"apos\"></input> POS tag<br>";
    print "<input type=\"checkbox\" name=\"aphon\"></input> Phon<br>";
    
    print "</td><td valign=\"top\">";
    print "<b>Metadata (alignment):</b><br>";
    print "<input type=\"checkbox\" name=\"atext_id\"></input> Text id<br>";
    print "<input type=\"checkbox\" name=\"asent_id\" checked></input> Sentence id<br>";
    print "<input type=\"checkbox\" name=\"aauthor\"></input> Author<br>";
    print "<input type=\"checkbox\" name=\"alanguage\"></input> Language<br>";
    print "<input type=\"checkbox\" name=\"adate\"></input> Publication date<br>";
}

print "</td></tr><tr><td valign=\"top\">";
print "<b>Annotation:</b><br>";
print "<select name=\"annotationset\">";
print "<option value=\"\" selected></option>";
print "<option value=\"__FREE__\">** free annotation **</option>";

my $sets_table = uc($corpus) . "annotation_sets";

# get sets
my $sth = $dbh->prepare(qq{ SELECT id, name FROM $sets_table;});

$sth->execute  || die "Error fetching data: $DBI::errstr";
while (my ($id, $name) = $sth->fetchrow_array) {
    print "<option value=\"$id\">$name</option>";
}
print "</select>";


print "</td></tr></table>";

print "<br>Format: <select name=\"format\"><option value=\"tsv\">Tab separated values</option><option value=\"csv\">Comma separated values</option><option value=\"xls\">Excel spreadsheet</option><option value=\"html\">HTML</option></select><br>";
print "<input type=\"submit\"></input>";
print "</form>";
print "<b>$sets_table</b>";
print "</body></html>";
