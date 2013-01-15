#!/usr/bin/perl

use CGI;
use Spreadsheet::WriteExcel;
use DBI;
use lib("/home/httpd/html/glossa/pm");
use Glossa_old;

my $corpus=CGI::param('corpus');
my $conf = Glossa::get_conf_file($corpus);
my %conf = %$conf;

my $user = $ENV{'REMOTE_USER'}; 
my $query_id = CGI::param('query_id');

# FIXME: this is a silly way of doing things
my $conf= $conf{'tmp_dir'} . "/" . $query_id . ".conf"; 
unless (-e $conf) {
  $conf{'tmp_dir'} = $conf{'config_dir'}  . "/" . $corpus . "/hits/"  . $user . "/";
}



print "Content-type: text/html\n\n";

print "<html><head></head><body>";
print "Result: ";

my $dsn = "DBI:mysql:database=$conf{'db_name'};host=$conf{'db_host'}";
$dbh = DBI->connect($dsn, $conf{'db_uname'}, $conf{'db_pwd'}, {RaiseError => 1})          ||              die $DBI::errstr;



my $annotation_set = CGI::param('annotationset');

my %annotation_value;
if ($annotation_set) {
    my $annotation_values_table = uc($corpus) . "annotation_values";

    my $sth = $dbh->prepare(qq{ SELECT id,value_name FROM $annotation_values_table where set_id = '$annotation_set';});
    $sth->execute  || die "Error fetching data: $DBI::errstr";
    while (my ($id,$value) = $sth->fetchrow_array) {
	$annotation_value{$id}=$value;
    }    
}


my $format = CGI::param('format');
my $out = $query_id . "." . $format;

$query_id = $query_id."_";
my @files = <$conf{'tmp_dir'}/$query_id*>; # AHA!!! There are more than one!!  !!!This doesn't work, as "file_2.txt" > "file_12.txt"

my $number_of_files = @files;#<$conf{'tmp_dir'}/$query_id*>;

#print "No. of files = $number_of_files<br />";
#print "$conf{'tmp_dir'}/$query_id<br />";
# a fix i did way back in the days.. joel
@files = ();
for (my $j = 1; $j <= $number_of_files; $j++ ){
    $files[$j-1] = "$conf{'tmp_dir'}/$query_id" . "$j.dat";
}

print "<a href=\"", $conf{'download_url'}, "/"; 
print $out, "\">", $out, "</a>";

$out = $conf{'dat_files'} . "/"  . $out;
print "FILEddd: $out<br />";

my $workbook;
if ($format eq "xls") { 
     $workbook = Spreadsheet::WriteExcel->new($out);
    $worksheet = $workbook->add_worksheet();
}


else { open (OUT, ">$out") or die(print "cannot open $out") }

if ($format eq "html") { print OUT "<table border=1>"; }

if (CGI::param('head')) {

    my @head;

    foreach my $cat ("text_id", "sent_id", "author", "language", "date") {
	if (CGI::param($cat)) { push @head, $cat } 
    }



    if (CGI::param('form') or CGI::param('pos') or CGI::param('lexeme') or CGI::param('phon')) { push @head, "Left context" }
    if (CGI::param('form') or CGI::param('pos') or CGI::param('lexeme') or CGI::param('phon') or CGI::param('mform') or CGI::param('mpos') or CGI::param('mlexeme') or CGI::param('mphon')) { push @head, "match" }
    if (CGI::param('form') or CGI::param('pos') or CGI::param('lexeme') or CGI::param('phon')) { push @head, "Right context" }


    
    foreach my $cat ("atext_id", "asent_id", "aauthor", "alanguage", "adate") {
	if (CGI::param($cat)) {
	    my $cat2 = $cat;
	    $cat2 =~ s/^a/Aligned /;
	    push @head, $cat2;
	    } 
    }
 
    if (CGI::param('aform') or CGI::param('apos') or CGI::param('alexeme') or CGI::param('aphon')) { push @head, "Aligned region" }

    if ($annotation_set) {
	push @head, "Annotation";
    }


    foreach my $h (@head) {
	$h = uc($h);
    }

    if ($format eq "html") { print OUT "<tr><td>", join ("</td><td>", @head), "</td></tr>"; }
    elsif ($format eq "tsv") { print OUT join ("\t", @head), "\n"; }
    elsif ($format eq "csv") {print OUT "\"", join ("\",\"", @head), "\"\n" }
    elsif ($format eq "xls") {

	my $format = $workbook->add_format(); # Add a format
	$format->set_bold();
#	$format->set_color('red');
	$format->set_align('center');

	my $j = 0;
	foreach my $el (@head) {
	    $worksheet->write(0,$j,$el,$format);
	    $j++;
	}

    }
    
}




my $i=0;
if (CGI::param('head')) { $i++ }



foreach my $f (@files) {


    open (FILE, $f);
#   print "FILE: $f<br />";
    $/="\n\n\n";
    while (<FILE>) {

	my @n;
#	print "$_<br />";
	my @lines = split(/\n/, $_);

	my $source = shift @lines;

	my ($c,$s_id,$sts_string,$left,$match,$right) = split(/\t/, $source);



	my @sts = split(/\|\|/, $sts_string);
	my %sts;
	foreach my $sts (@sts) {
	    my ($k,$v) = split(/=/, $sts);
	    $sts{$k}=$v;
	}

	# fixme: this is only accidentally correct (for some corpora)
	if (CGI::param('text_id')) { push @n, $sts{'text_id'} };
	if (CGI::param('sent_id')) { push @n, $s_id };
	

	# mer metadata ...
	# author, language, date
	foreach my $cat ("author", "language", "date") {
	    if (CGI::param($cat)) { 
		my $t_id = $sts{'text_id'};
		my $sth = $dbh->prepare(qq{ SELECT value FROM metadata where text = '$t_id' and category = '$cat';});
		$sth->execute  || die "Error fetching data: $DBI::errstr";
		my $tm = $sth->fetchrow_array;
		push @n, $tm;
	    }	    
	}

	my ($phon,$token,$pos,$lexeme);
	my $speech = 0;
	if( $corpus == 'scandiasyn' ){ $speech = 1 }

	my $left2;
	my @left = split(/ /, $left);
	foreach my $l (@left) {
	    ($token, $pos, $lexeme)=split(/\//,$l);
	    if($speech){
		($token, $lexeme, $phon, $pos)=split(/\//,$l);		
	    }
	    my @tmp;
	    if (CGI::param('form')) { push @tmp, $token };
	    if (CGI::param('pos')) { push @tmp, $pos };
	    if (CGI::param('lexeme')) { push @tmp, $lexeme };
	    if (CGI::param('phon')){push @tmp,$phon}
	    $left2 .= join("/", @tmp) . " ";
	}
	push @n, $left2;

	my $match2;
	my @match = split(/ /, $match);
	foreach my $m (@match) {
	    ($token, $pos, $lexeme)=split(/\//,$m);
	    if($speech){
		($token, $lexeme, $phon, $pos)=split(/\//,$m);		
	    }
	    my @tmp;
	    if (CGI::param('form') or CGI::param('mform')) { push @tmp, $token };
	    if (CGI::param('pos') or CGI::param('mpos')) { push @tmp, $pos };
	    if (CGI::param('lexeme') or CGI::param('mlexeme')) { push @tmp, $lexeme };
	    if(CGI::param('phon') or CGI::param('mphon')){push @tmp, $phon}
	    $match2 .= join("/", @tmp) . " ";
	}
	push @n, $match2;

	my $r2;
	my @r = split(/ /, $right);
	foreach my $r (@r) {
	    ($token, $pos, $lexeme)=split(/\//,$r);
	    if($speech){
		($token, $lexeme, $phon, $pos)=split(/\//,$r);		
	    }
	    my @tmp;
	    if (CGI::param('form')) { push @tmp, $token };
	    if (CGI::param('pos')) { push @tmp, $pos };
	    if (CGI::param('lexeme')) { push @tmp, $lexeme };
	    if(CGI::param('phon')){push @tmp,$phon}
	    $r2 .= join("/", @tmp) . " ";
	}
	push @n, $r2;


	if (CGI::param('align')) {
	    foreach my $a (@lines) {

		my ($c,$s_id,$sts_string,$al) = split(/\t/, $a);

		my @sts = split(/\|\|/, $sts_string);
		my %sts;
		foreach my $sts (@sts) {
		    my ($k,$v) = split(/=/, $sts);
		    $sts{$k}=$v;
		}

		if (CGI::param('atext_id')) { push @n, $sts{'text_id'} };
		if (CGI::param('asent_id')) { push @n, $s_id };

		# mer metadata ...
		foreach my $cat ("author", "language", "date") {
		    my $cat2 = "a" . $cat;
		    if (CGI::param($cat2)) { 
			my $t_id = $sts{'text_id'};
			my $sth = $dbh->prepare(qq{ SELECT value FROM metadata where text = '$t_id' and category = '$cat';});
			$sth->execute  || die "Error fetching data: $DBI::errstr";
			my $tm = $sth->fetchrow_array;
			push @n, $tm;
		    }	    
		}

		my $a2;
		my @a = split(/ /, $al);
		foreach my $aa (@a) {
		    my ($token, $pos, $lexeme)=split(/\//,$aa);
		    my @tmp;
		    if (CGI::param('aform')) { push @tmp, $token };
		    if (CGI::param('apos')) { push @tmp, $pos };
		    if (CGI::param('alexeme')) { push @tmp, $lexeme };
		    $a2 .= join("/", @tmp) . " ";
		}
		push @n, $a2;

	    }
	}

	
	# annotations

	if ($annotation_set) {
	    	my $annotation_table = uc($corpus) . "annotations";
#		print "SELECT value_id FROM $annotation_table where s_id = '$s_id' and set_id = '$annotation_set';\m";
		my $sth = $dbh->prepare(qq{ SELECT value_id FROM $annotation_table where s_id = '$s_id' and set_id = '$annotation_set';});
		$sth->execute  || die "Error fetching data: $DBI::errstr";
		my ($stored_value) = $sth->fetchrow_array;

		my $displayed_value;
		if ($annotation_set eq '__FREE__') {
		    $displayed_value = $stored_value;
		}
		else {
		    $displayed_value = $annotation_value{$stored_value};
		}
	
		push @n, $displayed_value;
	}

        if ($format eq "html") { print OUT "<tr><td>", join ("</td><td>", @n), "</td></tr>"; }
	elsif ($format eq "tsv") { print OUT join ("\t", @n), "\n" }
	elsif ($format eq "csv") {
	    $out =~ s/\"/\"\"\"/g;
	    my $out = "\"" . join ("\",\"", @n). "\"" . "\n";
	    print OUT $out;
	}
	elsif ($format eq "xls") {

	    my $j=0;
	    foreach my $el (@n) {
		$worksheet->write($i,$j,$el);
		$j++;
	    }
	    $i++;
	}



    }
    close FILE;

}


if ($format eq "html") { print OUT "</table>"; }




