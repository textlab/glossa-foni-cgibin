#!/usr/bin/perl

use CGI;
use Spreadsheet::WriteExcel;
use GD::Graph::bars;
use GD::Graph::hbars;
use GD::Graph::pie;

use lib("./lib/");
use Glossa_local;
use GlossaConfig;

print "Content-type: text/html\n\n";

print "<html><head></head><body>";

my $query_id = CGI::param('query_id');
my $user = $ENV{'REMOTE_USER'}; 
my $corpus = CGI::param('corpus');

my %conf = GlossaConfig::readConfig($corpus);

# FIXME: this is a silly way of doing things
my $conf= $conf{'tmp_dir'} . "/" . $query_id . ".conf"; 
unless (-e $conf) {
  $conf{'tmp_dir'} = $conf{'config_dir'}  . "/" . $corpus . "/hits/"  . $user . "/";
}



my $format = CGI::param('format');
my $cutoff = CGI::param('cutoff');
my $out = $query_id . "." . $format;
if ($format eq "bars") { $out =~ s/\.bars$/_\.png/ }
if ($format eq "pie") { $out =~ s/\.pie$/_\.png/ }
if ($format eq "hbars") { $out =~ s/\.hbars$/_\.png/ }

$query_id = $query_id."_";
my @files = <$conf{'tmp_dir'}/$query_id*>;



unless (($format eq "html") or ($format eq "bars") or ($format eq "pie") or ($format eq "hbars")) {
    print "<a href=\"", $conf{'download_url'}, "/";
    print $out, "\">", $out, "</a>";
}

if (($format eq "bars") or ($format eq "pie") or ($format eq "hbars")) {
    print "<img src=\"", $conf{'download_url'}, "/";
    print $out, "\">";
}


$out = $conf{'dat_files'} . "/" . $out;
unlink($out);

my %data;

my $workbook;
my $graph;
if ($format eq "xls") { 
    $workbook = Spreadsheet::WriteExcel->new($out);
    $worksheet = $workbook->add_worksheet();
}


open (OUT, ">$out");



foreach my $f (@files) {
    open (FILE, $f);

    my $i=0;

    $/="\n\n\n";
    while (<FILE>) {
	my @n;

	my @lines = split(/\n/, $_);

	my $source = shift @lines;
	my ($c,$s_id,$sts_string,$left,$match,$right) = split(/\t/, $source); # only $match is actually used.
	my $match2;
	my @match = split(/ /, $match);
#20130821 generalized. see count_choose.cgi
#need something like this in download.cgi
	foreach my $m (@match) {
	    my @tmp;
	    my @attributes = split /\//, $m;
	    my @att_params = CGI::param('attributes');
	    foreach my $att (@att_params){
		push @tmp, $attributes[$att];
	    }
	    $match2 .= join("/", @tmp) . " ";
	}
	unless (CGI::param('case')) { $match2 = lc($match2) }
	$data{$match2}++;
    }
    close FILE;

}

my @list;
while (my ($k,$v) = each %data) {
    push @list, [$k,$v];
}

my @list_sorted = sort { $b->[1] <=> $a->[1] } @list;

if ($cutoff) {
    splice(@list_sorted, $cutoff);
}    

if ($format eq "tsv") { 

    if (CGI::param('head')) {
	print OUT "Occurences\tString\n";
    }
    foreach my $e (@list_sorted) {
	print OUT "$e->[1]\t$e->[0]\n";
    }
}
elsif ($format eq "csv") {
    if (CGI::param('head')) {
	print OUT "\"Occurences\",\"String\"\n";
    }
    foreach my $e (@list_sorted) {
	$e->[0] =~ s/\"/\"\"\"/g;
	print OUT "\"$e->[1]\",\"$e->[0]\"\n";
    }
}
elsif (($format eq "bars") or ($format eq "pie") or ($format eq "hbars")) {

    my @x; my @y;
    my $max_y=0;
    my $max_length_x;
    my $no_labels = @list_sorted;
    foreach my $e (@list_sorted) {
	push @y, $e->[1];
	if ($e->[1] > $max_y) { $max_y = $e->[1] }
	push @x, $e->[0];
	if (length($e->[0]) > $max_length_x) { $max_length_x = length($e->[0]) }	
    }

    if ($max_y > 1) { $div = 10 }
    if ($max_y > 100) { $div = 100 }
    if ($max_y > 1000) { $div = 1000 }
    if ($max_y > 10000) { $div = 10000 }
    if ($max_y > 100000) { $div = 100000 }

    my $dec = $max_y / $div;
    $max_y = int($dec + 1);
    $max_y = $max_y * $div;


    my $graph_width = ($max_length_x * 5) * $no_labels; 

    if ($graph_width < 150) { $graph_width = 150 }

    my $vertical;
    if ($graph_width > 800) {
	$vertical = 1;
	$graph_width = $no_labels * 20;
    }

    my $graph;
    if ($format eq "bars") {
	$graph = GD::Graph::bars->new($graph_width, 400);
	$graph->set( 
		     x_label           => 'String',
		     y_label           => 'Occurences',
		     y_max_value           => $max_y,
		     x_labels_vertical => $vertical,
		     title             => "Lexical Statistics"
		     ) or die $graph->error;

    }
    if ($format eq "hbars") {
	$graph_heigth = $no_labels * 15;
	if ($graph_heigth < 100) { $graph_heigth = 100 }
	$vertical=0;
	$graph = GD::Graph::hbars->new(750, $graph_heigth);
	$graph->set( 
		     x_label           => 'String',
		     y_label           => 'Occurences',
		     y_max_value           => $max_y,
		     x_labels_vertical => $vertical,
		     title             => "Lexical Statistics"
		     ) or die $graph->error;

    }
    if ($format eq "pie") {
        $graph = GD::Graph::pie->new(400, 400);
        $graph->set(title => "Lexical Statistics") or die $graph->error;
    }

    my @data = (\@x, \@y);

    my $gd = $graph->plot(\@data) or die $graph->error;

    binmode OUT;
    print OUT $gd->png;
    close OUT;

}
elsif ($format eq "xls") {

    my $j=0;
    if (CGI::param('head')) {
	my $format = $workbook->add_format(); # Add a format
	$format->set_bold();
	$format->set_align('center'); 
	$worksheet->write(0,0,"Occurences",$format);
	$worksheet->write(0,1,"String",$format);
	$j++;
    }
    foreach my $e (@list_sorted) {
	$worksheet->write($j,0,$e->[1]);
	$worksheet->write($j,1,$e->[0]);
	$j++;
    }

}
elsif ($format eq "html") {
    print "<table><tr><td><b>occurences</b> &nbsp;</td><td><b>match</b></td></tr>";
    
    foreach my $e (@list_sorted) {
	my $res = $e->[0];
	$res =~ s/\// - /g;
	print "<tr><td align=\"right\">$e->[1] &nbsp;</td><td><b>$res</b></td></tr>";
    }

    print "</table>"; 

}

chmod(0755,$out);

print "</body></html>";
