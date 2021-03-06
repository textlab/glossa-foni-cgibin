#!/usr/bin/perl

use CGI;

use lib ('./lib/');
use Glossa_local;
use GlossaConfig;

print "Content-type: text/html\n\n";

my $query_id = CGI::param('query_id');
my $db_name = CGI::param('db_name');
my $corpus = CGI::param('corpus');
my $base_corpus = CGI::param('base_corpus');

my %conf = GlossaConfig::readConfig($corpus);

my $ngram = CGI::param('ngram');

my @corpus_attributes = split / /,  $conf{'corpus_attributes'};

my @corpus_attributes_name = @corpus_attributes;
if($conf{'corpus_attributes_name'}){
    @corpus_attributes_name = split /\t/,  $conf{'corpus_attributes_name'};
}
my $corpus_attributes_ref = {};
my $j = 0;
foreach my $k (@corpus_attributes){
    my $name = $corpus_attributes_name[$j++];
    $name =~s/ default//;
     $corpus_attributes_ref->{$k} = $name;
}

print "<html><head></head><body>";

print "<form action=\"", $conf{'cgiRoot'}, "/coll2.cgi\" method=\"get\">";
print "<input type=\"hidden\" name=\"query_id\" value=\"$query_id\">";
print "<input type=\"hidden\" name=\"corpus\" value=\"$corpus\">";
print "<input type=\"hidden\" name=\"base_corpus\" value=\"$base_corpus\">";

print "<table cellpadding=\"15\"><tr><td>";
print "<input type=\"checkbox\" name=\"case\">Case sensitive</input><br>";
print "<input type=\"checkbox\" name=\"globalstats\">Use global lexical statistics (only bigrams)</input>";

print "</td><td valign=\"top\">";
print "<b>Collocates:</b><br>";
print "<input type=\"checkbox\" name=\"pos\"></input>  $corpus_attributes_ref->{'pos'}";
print "<input type=\"checkbox\" name=\"lexeme\"></input>  $corpus_attributes_ref->{'lemma'} ";
print "<input type=\"checkbox\" name=\"form\" checked></input> ".$corpus_attributes_ref->{'word'};

print "</td></tr></table>";

print "&nbsp;&nbsp;&nbsp;&nbsp;<b>Context:</b>";
print "<table cellpadding=\"15\"><tr><td>";

print "<input type=\"radio\" name=\"ngram\" value=\"2\" checked></input>bigram<br>";

print "Statistical measure:<br>";
print "<select name=\"measure_bi\">";
print "<option value=\"freq\">Frequency</option>";
print "<option value=\"dice\" selected>Dice Coefficient</option>";
print "<option value=\"leftFisher\">Fishers exact test - left sided</option>";
print "<option value=\"rightFisher\">Fishers exact test - right sided</option>";
print "<option value=\"ll\">Log-likelihood ratio</option>";
print "<option value=\"tmi\">Mutual Information</option>";
print "<option value=\"pmi\">Pointwise Mutual Information</option>";
print "<option value=\"odds\">Odds Ratio</option>";
print "<option value=\"phi\">Phi Coefficient</option>";
print "<option value=\"tscore\">T-score</option>";
print "<option value=\"x2\">Pearson\'s Chi Squared Test</option>";
print "</select>";

print "<br>Window size: ";
print "<input type=\"text\" name=\"window\" value=\"2\" size=\"2\"></input>";

print "</td><td valign=\"top\">";
print "<input type=\"radio\" name=\"ngram\" value=\"3\"></input>trigram <br>";

print "Statistical measure:<br>";

print "<select name=\"measure_tri\">";
print "<option value=\"freq\">Frequency</option>";
print "<option value=\"ll3\" selected>Log-likelihood ratio</option>";
print "</select>";

print "</td></tr></table>";

print "<table cellpadding=\"10\"><tr><td>";

print "<b>Cutoff:</b><br>";
print "Maximum number of results: <input type=\"text\" name=\"cut_max\" value=\"1000\" size=\"4\"></input> <br>";
print "Minimum association value: <input type=\"text\" name=\"cut_min\" size=\"3\"></input> <br>";
print "Minimum no of occurences: <input type=\"text\" name=\"cut_occ\" size=\"3\"></input> <br><br>";

print "</td><td valign=\"top\">";

print "</td></tr></table>";

print "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<input type=\"reset\"></input> <input type=\"submit\"></input><br>";
print "</form>";
print "</body></html>";
