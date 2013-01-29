#!/usr/bin/perl

use CGI;
use DBI;
use Data::Dumper;
use strict;
use POSIX qw(locale_h);

use lib ('./lib/');
use Glossa_local;

setlocale('LC_TYPE', "norweigan");

select(STDOUT);
$|=1;


my $cgi = CGI->new;
# FIXME: this should be done in module
my %cgi_hash;
my @prms = $cgi->param();

my $test = 0;

#catch all the post vars in a hash

foreach my $p (@prms) {
    my $p2 = $p;
    $p2 =~ s/\[\]$//;
    my @vals = $cgi->param($p);
    if($test){ print "<br />$p - @vals";  }
    $cgi_hash{$p2}=\@vals;
}


# creates hash de le hash

my $in = Glossa::create_cgi_hash2(\%cgi_hash);
my %in = %$in;

my %meta = $in{"meta"};

my $CORPUS = $in{'query'}->{'corpus'}->[0];

print "Content-type: text/html; charset=" . ($CORPUS =~ /^(run|skriv)$/ ? "UTF-8" : "ISO-8859-1") . "\n\n";
print "<html>\n<head>\n</head>\n<body>\n";

my %conf = Glossa::readConfig($CORPUS);

my $corpus_mode = $conf{'corpus_mode'};

my $speech_corpus = 0;

if($corpus_mode eq 'speech'){
    $speech_corpus = 1;
}

my $dsn = "DBI:mysql:database=$conf{'db_name'};host=$conf{'db_host'}";
my $dbh = DBI->connect($dsn, $conf{'db_uname'}, $conf{'db_pwd'}, {RaiseError => 1})          ||              die $DBI::errstr;

my $format = CGI::param('format');

my ($subcorpus,$sql_query_nl,$texts_allowed) = Glossa::create_tid_list(\%conf, \%in, $CORPUS);


my $text_table = uc($CORPUS) . "text";
my $author_table = uc($CORPUS) . "author";
my $class_table = uc($CORPUS) . "class";

my %texts_allowed = %$texts_allowed;
my @tids = keys %texts_allowed;


my $infs = @tids; # joel 20071211

my @meta_class = split(/ /, $conf{'meta_class'});
foreach my $m (@meta_class) {
    $m = $class_table . "." . $m;
}
my $class_select = join(", ", @meta_class);

my @meta_author = split(/ /, $conf{'meta_author'});
foreach my $m (@meta_author) {
    $m = $author_table . "." . $m;
}
my $author_select = join(", ", @meta_author);


print "<div id='stats'>\n</div>\n";

print ($speech_corpus ? "Informanter: $infs<br />" : "Tekster: $infs<br />"); # joel 20071211; anders 20110125

my $cnt_select = 0;
if ($CORPUS eq "skriv") {
  my $word_count = $dbh->selectrow_array("SELECT MAX(endpos)+1 FROM SKRIVtext");
  print "Antall ord: $word_count";
  $cnt_select = 1;
}

print "<hr>\n<table style='border-width:1px;border-style:outset;border-color:#afaeae;padding:0px;margin:0px'>\n";
print "<tr>\n";
my @meta_text = split(/ /, $conf{'meta_text'});

foreach my $m (@meta_text) {
    print "<td>\n<b>", $m, "</b>\n</td>\n";
    #$m = $text_table . "." . $m;
}
my $text_select = join(", ", @meta_text);

my @meta_text_sum = split(/ /, $conf{'meta_text_sum'});

if ($cnt_select) {
    print "<td>\n<b>word count</b>\n</td>\n";
}

if ($class_select) {
    print "<td>\n<b>class</b>\n</td>\n";
}
if ($author_select) {
    print "<td>\n<b>author</b>\n</td>\n";
}


print "<tr>\n";


my @tids_sorted = sort @tids;


my %stats;


my $bg = "#fff";
foreach my $tid (@tids_sorted) {

    my $table = $text_table;;
    if($speech_corpus){ $table = $author_table; }
    my $sql_query = "SELECT * FROM $table WHERE tid = '$tid';";

    my $sth = $dbh->prepare($sql_query);
    $sth->execute  || die "Error fetching data: $DBI::errstr";

    my $r = $sth->fetchrow_hashref;
    my %r = %$r;

    my @r;
    foreach my $col (@meta_text) {

	push @r, $r{$col}
    }

    foreach my $col (@meta_text_sum) {
	my $cont = $r{$col};
	$stats{$col}->{$cont}+=$r{'wordcount'};
    }
    $stats{'ALL'}->{'ALL'}+=$r{'wordcount'};

    if ($bg eq "#fff") { # joel 20071211
	$bg = "#ddd";
    }
    else {
	$bg = "#fff";
    }
    print "<tr style='background-color:$bg'>\n";
    print "<td>\n";
    print join("</td>\n<td>\n", @r);
    print "</td>\n";
    
    if ($cnt_select) {
        my $word_count = $r{'endpos'}-$r{'startpos'}+1;
        print "<td>$word_count</td>\n";

            my $identifier = $r{'tid'};
            my $source_line = "";
            my $assignment_code = join("_", (split("_", $identifier))[1,2]);
            my $assignment_path = "/michalkk/skriv/oppgavetekster/${assignment_code}.pdf";

	    $source_line.=sprintf("<font size=\"-2\">\n<a href=\"#\" onClick=\"window.open('$conf{'htmlRoot'}/html/profile.php?tid=$identifier&corpus=$CORPUS',");
	    $source_line.=sprintf("'mywindow','height=600,width=600,status,scrollbars,resizable');\"><img src='$conf{'htmlRoot'}/html/img/i.gif' alt='i' border='0'></a>&nbsp;</font>");

            if (-e "/var/www/html$assignment_path") {
                $source_line.=sprintf("<a href=\"$assignment_path\" target=\"_new\"><img src=\"/michalkk/skriv/img/assignment-text.png\" height=\"14\"/></a>&nbsp;");
            }
            my $identifier_noslash = $identifier;
            $identifier_noslash =~ s,/,_,g;
            my $answer_path = "/michalkk/skriv/oppgavesvar/${identifier_noslash}.pdf";
            if (-e "/var/www/html$answer_path") {
                $source_line.=sprintf("<a href=\"$answer_path\" target=\"_new\"><img src=\"/michalkk/skriv/img/assignment-answer.png\" height=\"14\"/></a>");
            }
            print "<td>$source_line</td>";
    }
	

    if ($class_select) {
	# FIXME: at det er den første kommer an på cgi.conf
	my $sql = "SELECT $class_select from $class_table where $class_table.tid='$r[0]';";
	
	my $sth2 = $dbh->prepare($sql);
	$sth2->execute  || die "Error fetching data: $DBI::errstr";
	
	print "<td>\n";
	my @res;
	while (my ($r2) = $sth2->fetchrow_array) { push @res, $r2 }
	print join("<hr>\n", @res);
	print "</td>\n";
}

    if ($author_select) {
	# FIXME: at det er den første kommer an på cgi.conf
	my $sql = "SELECT $author_select from $author_table where $author_table.tid='$r[0]';";
	
	my $sth2 = $dbh->prepare($sql);
	$sth2->execute  || die "Error fetching data: $DBI::errstr";
	
	print "<td>\n";
	my @res;
	while (my (@r2) = $sth2->fetchrow_array) { my $tmp = join(" ", @r2); push @res, $tmp; }
	print join("<hr>\n", @res);
	print "</td>\n";
	
    }    

    print "<tr>\n";
    
}



print "</table>\n";


while (my ($k, $v) = each %stats) {
    print "<b>$k</b>\n";
    print "<table>\n";

    my @list;
    my $total;
    while (my ($k2, $v2) = each %$v) {
	$total+=$v2;
	push @list, [$k2, $v2];
    }

    my @list_sorted = sort {$a->[0] cmp $b->[0]} @list;

    foreach my $entry (@list_sorted) {
	my $pct = ($entry->[1]/$total)*100;
	$pct = sprintf("%.1f", $pct);
	print "<tr>\n<td width=200>\n" . $entry->[0] . "</td>\n<td>\n" . $entry->[1] . "</td>\n<td>\n" . $pct . "</td>\n</tr>\n";
    }

    print "</table>\n<br>\n\n";

}
print "</body>\n</html>\n";
