#!/usr/bin/perl

use CGI;
use locale;
use LWP::Simple;
use locale;
use POSIX qw(locale_h);
setlocale(LC_ALL, "norwegian");

use lib ('./lib/');
use Glossa_local;
use GlossaConfig;

my $corpus=CGI::param('corpus');
my $user = $ENV{'REMOTE_USER'}; 
my $query_id = CGI::param('query_id');

my %conf=GlossaConfig::readConfig($corpus);

# FIXME: this is a silly way of doing things
my $conf= $conf{'tmp_dir'} . "/" . $query_id . ".conf"; 
unless (-e $conf) {
  $conf{'tmp_dir'} = $conf{'config_dir'}  . "/" . $corpus . "/hits/"  . $user . "/";
}

print "Content-type: text/html\n\n";

my $query_id2 = $query_id."_";
my @files = <$conf{'tmp_dir'}/$query_id2*>;

my @data;

my $pri = CGI::param('primary');
my $sec = CGI::param('secondary');

foreach my $f (@files) {
    open (FILE, $f);

    $/="\n\n\n";
    while (<FILE>) {
        my $dat = $_;
        my $pri_dat;
        my $sec_dat;

        my @lines = split(/\n/, $_);
        my $source = shift @lines;
        my ($c, $t,$s,$left,$match,$right) = split(/\t/, $source);


#more alterations 20130909
	my @sts = split(/\|\|/, $s);
	my %sts;
	my $pos1 = CGI::param('pos1');
	unless ($pos1) { $pos = 1 }
	my $pos2 = CGI::param('pos2');
	unless ($pos2) { $pos2 = 1 }
	foreach my $sts (@sts) { #hash all sts_string values, eg text_id=aaseral_04gk..
	    my ($k,$v) = split(/=/, $sts);
	    $sts{$k}=$v;
	}



        if ($pri =~ /sort_(.+)/) {
	    my $by = $1;
#$s is all structures, not s_id	    
            $pri_dat=$sts{$by};
        }
        elsif ($pri eq "random") {
            $pri_dat=rand();
        }
        else {
	    my $list;
	    if ($pri eq "left") {
		$list=$left;
		$pos1 = - $pos1;
            }
            elsif ($pri eq "match") {
                $list=$match;
                $pos1 = $pos1-1;
            }
            elsif ($pri eq "right") {
                $list=$right;
                $pos1 = $pos1-1;
            }
	    
            my @to_sort;
            my @list = split(/ /, $list);
            if ($pri eq "match") {
                @to_sort = @list;
            }
            else {
                push @to_sort, $list[$pos1];
            }
	    
            my @to_sort2;
            foreach my $token (@to_sort) {

#need to make changes here!!!

#here we have to capture the attribute required by index (as given in the sort_choose.cgi sort_attributes array), rather than using the hardcoded param names (form_inl, pos_in1 etc)
		my @components = split(/\//, $token);
		my @att_params = CGI::param('sort_attributes');
		foreach my $att (@att_params){
		    push @to_sort2, $components[$att];
		}
            }

            $pri_dat .= join("/", @to_sort2) . " ";	    
        }

        if ($sec =~ /sort_(.+)/) {
	    my $by = $1;
            $sec_dat=$sts{$by};
        }
        else {
            my $list;

            if ($sec eq "left") {
                $list=$left;
                $pos2 = - $pos2;
            }
            elsif ($sec eq "match") {
                $list=$match;
                $pos2 = $pos2-1;
            }
            elsif ($sec eq "right") {
                $list=$right;
                $pos2 = $pos2-1;
            }

            my @to_sort;
            my @list = split(/ /, $list);

            if ($sec eq "match") {
                @to_sort = @list;
            }
            else {
                push @to_sort, $list[$pos2];
            }

            my @to_sort2;

            foreach my $token (@to_sort) {
		my @components = split(/\//, $token);
		my @att_params = CGI::param('sort_attributes2');
		foreach my $att (@att_params){
		    push @to_sort2, $components[$att];
		}
            }
            $sec_dat .= join("/", @to_sort2) . " ";	    
        }

        unless (CGI::param('case')) {
            $pri_dat = lc($pri_dat);
            $sec_dat = lc($sec_dat);
        }
        push @data, [$pri_dat,$sec_dat,$dat];

    }
    close FILE;
}

my @data_sorted = sort { $a->[0] cmp $b->[0] || $a->[1] cmp $b->[1] } @data;

my $i=2;
my $j=0;

my $filename = $conf{'tmp_dir'} . "/" . $query_id . "_1.dat";
open (OUT, ">$filename");

foreach my $e (@data_sorted) {
    $j++;
    print OUT $e->[2];

    if ($j==20) { 
        close OUT;
        $filename = $conf{'tmp_dir'} . "/" . $query_id . "_" . $i . ".dat";
        open (OUT, ">$filename");
        $j=0;
        $i++;
    }
}

print "<script language='javascript'>";
print "window.location='", $conf{'cgiRoot'}, "/show_page_dev.cgi?n=1&query_id=$query_id&corpus=", $corpus, "';";
print "</script>";


