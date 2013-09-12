#!/usr/bin/perl

use CGI;
use Data::Dumper;

use lib("./lib/");
use Glossa_local;
use GlossaConfig;

print "Content-type: text/html\n\n";

my $corpus = CGI::param('corpus');
my $base_corpus = CGI::param('base_corpus');

my %conf = GlossaConfig::readConfig($corpus);

my $query_id = CGI::param('query_id');

my @corpus_attributes = split / /,  $conf{'corpus_attributes'};

#20130821
#added corpus_attributes_name to cgi.conf
#this to give a sensible name, while not having to hardcode the name into this code (eg if lemma, lexeme)
#all the attributes to be displayed must have a name, matching by position their attribute
#example:
#corpus_attributes = word lemma phon pos gender num type defn temp pers case degr descr nlex mood voice id
#corpus_attributes_name = Word form      Lemma   _       Part of speech
#where blanks are skipped in the list of displayable attributes
#corpus_arrtibutes_name is tab-seperated, not space.

my @corpus_attributes_name = @corpus_attributes;
if($conf{'corpus_attributes_name'}){
    @corpus_attributes_name = split /\t/,  $conf{'corpus_attributes_name'};
}
my $corpus_attributes_ref = {};
my $j = 0;
foreach my $k (@corpus_attributes_name){
    if($k eq '_'){$j++; next};
    $corpus_attributes_ref->{$k} = $j++;
}

print "<html><head></head><body>";
print "<form action=\"", $conf{'cgiRoot'}, "/count.cgi\" method=\"get\">";
print "<input type=\"hidden\" name=\"query_id\" value=\"$query_id\">";
print "<input type=\"hidden\" name=\"corpus\" value=\"$corpus\">";

print "<input type=\"checkbox\" name=\"case\" checked></input> Case sensitive<br>";
print "<input type=\"checkbox\" name=\"head\" checked></input> Create headings<br>";

print "<br><b>Include:</b><br>";
my $i = 0;
foreach my $corpus_attributes_name (@corpus_attributes_name){
    if($corpus_attributes_name eq '_'){	$i++; next }
    my $checked = "";
    if($corpus_attributes_name =~ /default/){ $corpus_attributes_name =~ s/ default//; $checked = "checked" } # set default
    print "<input type=\"checkbox\" name=\"attributes\" value=\"".$i++."\" $checked></input> " . ucfirst($corpus_attributes_name) . "<br>";
}
print "<br>Max number of results: <input type=\"text\" name=\"cutoff\" size=\"4\"></input><br>"; 
print "<br>Output format:<br> <select name=\"format\"><option value=\"html\" selected>HTML</option><option value=\"tsv\">Tab separated values</option><option value=\"csv\">Comma separated values</option><option value=\"xls\">Excel spreadsheet</option><option value=\"bars\">Histogram</option><option value=\"hbars\">Histogram (horisontal)</option><option value=\"pie\">Pie chart</option></select><br><br><input type=\"submit\"></input><br>";
print "</form>";
print "</body></html>";
