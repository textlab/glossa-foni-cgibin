#!/usr/bin/perl

use CGI;

use lib ('./lib/');
use Glossa_local;
use GlossaConfig;

print "Content-type: text/html\n\n";
my $query_id = CGI::param('query_id');
my $corpus=CGI::param('corpus');

my %conf = GlossaConfig::readConfig($corpus);


#20130821
#added corpus_attributes_name to cgi.conf
#this to give a sensible name, while not having to hardcode the name into this code (eg if lemma, lexeme)
#all the attributes to be displayed must have a name, matching by position their attribute
#example:
#corpus_attributes = word lemma phon pos gender num type defn temp pers case degr descr nlex mood voice id
#corpus_attributes_name = Word form      Lemma   _       Part of speech
#where blanks are skipped in the list of displayable attributes
#corpus_arrtibutes_name is tab-seperated, not space.

#added 20130909

my $sort_on = $conf{'sort_on'};
if( !$sort_on ){
    $sort_on = 's_id(sentence id)';
}
=pod
my @corpus_structures = split / /, $conf{'corpus_structures'};
my @corpus_structures_name = split / /, $conf{'corpus_structures'};
if($conf{'corpus_structures_name'}){
    @corpus_structures_name = split /\t/,  $conf{'corpus_structures_name'};
}

my @meta_text = split / /, $conf{'meta_text'};
my @meta_text_name = split / /, $conf{'meta_text'};
if($conf{'meta_text_alias'}){
    @meta_text_name = split /\t/,  $conf{'meta_text_alias'};
}
=cut

my @corpus_attributes = split / /,  $conf{'corpus_attributes'};
my @corpus_attributes_name = @corpus_attributes;
if($conf{'corpus_attributes_name'}){
    @corpus_attributes_name = split /\t/,  $conf{'corpus_attributes_name'};
}

print "<html>\n<head>\n</head>\n<body>\n";

print "<form action=\"", $conf{'cgiRoot'}, "/sort.cgi\" method=\"get\">\n";
print "<input type=\"hidden\" name=\"query_id\" value=\"$query_id\"></input>\n";
print "<input type=\"hidden\" name=\"corpus\" value=\"$corpus\"></input>\n";

print "<input type=\"checkbox\" name=\"case\">Case sensitive</input><br><br>\n";


print "<b>Sort by:</b><br>\n";
print "<select name=\"primary\">\n";
print " <option value=\"left\">Left context</option>\n";
print " <option value=\"match\" selected>Match</option>\n";
print " <option value=\"right\">Right context</option>\n";


my ($struct,$name) = split /-/,$sort_on;
print " <option value=\"sort_$struct\">$name</option>\n";
#print " <option value=\"text_id\">TEXT ID</option>\n";
print " <option value=\"random\">randomize</option>\n";
print "</select>\n";


print "<br><input type=\"text\" name=\"pos1\" size=\"2\"></input> Position in context (counting from match)<br>\n";

#change this bit!!
print "Features used on tokens:<br>\n";

my $i = 0;
foreach my $corpus_attributes_name (@corpus_attributes_name){
    if($corpus_attributes_name eq '_'){	$i++; next }
    my $name = $corpus_attributes_name;
    my $checked = ($name =~ s/ default// ? "checked" : "");
    print "<input type=\"checkbox\" name=\"sort_attributes\" value=\"".$i++."\" $checked></input> " . ucfirst($name) . "<br>\n";
}

#print "<br><input type=\"checkbox\" name=\"form_in1\" checked>Word Form</input>\n";
#print "<input type=\"checkbox\" name=\"pos_in1\">Part-of-Speech</input>\n";
#print "<input type=\"checkbox\" name=\"lexeme_in1\">Lexeme</input><br>\n";
#end




print "<br><b>Sort by (secondary):</b><br>\n";
print "<select name=\"secondary\">\n";
print " <option value=\"\" selected></option>\n";
print " <option value=\"left\">Left context</option>\n";
print " <option value=\"match\">Match</option>\n";
print " <option value=\"right\">Right context</option>\n";
print " <option value=\"sort_$struct\">$name</option>\n";
#print " <option value=\"sent_id\">Sentence ID</option>\n";
print "</select>\n";
print "<br><input type=\"pos2\" size=\"2\"></input> Position in context (counting from match)<br>\n";

#and this bit here!!
print "Features used on tokens:<br>\n";
my $i = 0;
foreach my $corpus_attributes_name (@corpus_attributes_name){
    if($corpus_attributes_name eq '_'){	$i++; next }
    my $checked = "";
    if($corpus_attributes_name =~ /default/){ $corpus_attributes_name =~ s/ default//; $checked = "checked" } # set default
    print "<input type=\"checkbox\" name=\"sort_attributes2\" value=\"".$i++."\" $checked></input> " . ucfirst($corpus_attributes_name) . "<br>\n";
}
#print "<br><input type=\"checkbox\" name=\"form_in2\">Word Form</input>\n";
#print "<input type=\"checkbox\" name=\"pos_in2\">Part-of-Speech</input>\n";
#print "<input type=\"checkbox\" name=\"lexeme_in2\">Lexeme</input><br>\n";
#end



print "<br><input type=\"reset\"></input>\n";
print " <input type=\"submit\"></input><br>\n";
print "</form>\n";
print "</body>\n</html>\n";
