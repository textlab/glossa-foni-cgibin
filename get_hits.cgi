#!/usr/bin/perl

#get tits? hrmph hrmph

use CGI;
use strict;
use File::Copy;
use lib ('./lib/');
use Glossa_local;
use GlossaConfig;
use Data::Dumper;
use Scalar::Util qw(reftype);

select(STDOUT);
$|=1;

print "Content-type: text/html\n\n";

my $corpus=CGI::param('corpus');
my $user = $ENV{'REMOTE_USER'}; 
my $player = CGI::param('player'); 

my %conf = GlossaConfig::readConfig($corpus);

print "<html>\n<head>\n";
print "<script language=\"JavaScript\" src=\"", $conf{'htmlRoot'}, "/js/misc.js\"></script>\n";
print "</head>\n<body>\n";

my $hits_dir = $conf{'config_dir'} . "/" . $corpus . "/hits/" . $user . "/";


my $action = CGI::param('action');

if ($action eq 'delete') {

    my $for_deletion = $hits_dir . "/" . CGI::param('for_deletion');


    print "DELETING: $for_deletion<br>";

    my $backupdir = $hits_dir . "/backup"; 
    mkdir($backupdir);
    `mv $for_deletion* $backupdir`;

}

if ($action eq 'rename') {

    my $newname = CGI::param('newname');
    my $for_renaming = CGI::param('for_renaming');    

    if ($newname eq 'null') { $newname = 0 }

    if ($newname) {
    
	print "RENAMING $for_renaming to $newname<br>";

	    
	my $rename;
	my $conf = $hits_dir . "/" . $for_renaming . ".conf";    
	my $newconf = $conf . ".new";
	open (NEWCONF, ">$newconf");
	    
	open (CONF, $conf);
	while (<CONF>) {
	    chomp;
	    my ($key,$val) = split(/\s*=\s*/, $_);
	    if (($key eq "name")) {
		next if ($val eq $newname);
		$val = $newname;
		$rename = 1;
	    }
	    next unless $key;
	    print NEWCONF $key, " = ", $val, "\n";
	}
	close CONF;
	close NEWCONF;
	
	if ($rename) {
	    move($newconf,$conf);
	}
	

    }
    else {
	print "Can't rename to nothing.";
    }
}
# start of join ----------------
if ($action eq 'join') {
    my %sets;
    my $newname = CGI::param('newname');
    my @join = CGI::param('joinme');
    my $new_query_id = Glossa::createQueryId();
    my $firstjoin = $hits_dir . "/" . $join[0] . ".conf";
    my $newconf = $hits_dir . "/" . $new_query_id . ".conf";
    open (FIRST, $firstjoin); 
    open (NEW, ">$newconf");
    while (<FIRST>) {
	#go through first conf, writting all to NEW accept "name", which shall be "newname"
	my ($key,$val) = split(/\s*=\s*/, $_);
	if ($key eq 'name') {
	    print NEW "name=", $newname, "\n";
	}
	else {
	    print NEW;
	}
    }
    my $firsttop = $hits_dir . "/" . $join[0] . ".top";
    my $newtop = $hits_dir . "/" . $new_query_id . ".top";


#FIRST, BUILD NEW JSON COMPRISING ALL THE OTHERS.. BIT TRICKY
    my @refs;
    foreach my $i (@join){
	local $/ = undef;
	my $itop = "$hits_dir/$i.top";
	open(ITOP, $itop);
        $itop = <ITOP>;
	$itop =~ s/^.*var mapObj =//s; # get rid of all before..
	$itop =~ s/<\/script>.*$//s;   # ..and after
	my $ref = json_to_hash( $itop );
	push @refs, $ref;
	close ITOP;
    }
    my $ref = merge_hashes(shift @refs, shift @refs); #first two hash refs to merge
    while(my $r = shift @refs){ # the rest
	$ref = merge_hashes($ref, $r);
    }
    my $new_json = "\nvar mapObj = ";
    $new_json .= blessed_be_the_json($ref);
    $new_json .= ";\n";
#END OF BUILD NEW JSON...

    open (FIRST, $firsttop);
    open (NEW, ">$newtop");
    while (<FIRST>) { # write new top without the old top specifics
	s/<script>/<script type=\"text\/javascript\">/;
	s/query_id=\d+_\d+/query_id=$new_query_id/;
	s/<b>.*?<\/b>//;
	s/Hits found:.*?<br>//;
	s/^Results pages.*/<br>/;
	s/var mapObj/$new_json\nvar mapObj_old/;
	print NEW;
    }
    my $new_dat_id=0;

    foreach my $query_id (@join) {

	$query_id = $hits_dir . "/" . $query_id;

	my @files = <$query_id*.dat>;
	foreach my $file (@files) {
	    $new_dat_id++;
	    my $newfilename = $hits_dir . "/" .  $new_query_id . "_" . $new_dat_id . ".dat";
	    copy($file,$newfilename);
	    print NEW "<a id='page_$new_dat_id' href='show_page_dev.cgi?n=", $new_dat_id, "&query_id=", $new_query_id, "&corpus=$corpus'>", $new_dat_id, "</a>\n";
#	    print NEW "<a id='page_$new_dat_id' href='http://omilia.uio.no/cgi-bin/glossa//show_page_dev.cgi?n=", $new_dat_id, "&query_id=", $new_query_id, "&corpus=$corpus'>", $new_dat_id, "</a>\n";
	}
    }

    sub blessed_be_the_json{ #just regexp the dump into json.
	$ref = shift;
	my $json = Dumper($ref);
	$json =~ s/^\$VAR1 = bless\(//;
	$json =~ s/, 'JS_hash' \);//;
	$json =~ s/([^\s]+) => \d(,?)/$1$2/g;
	$json =~ s/([^\s]+) => bless\( {([^{}]*)\s*}, 'JS_array' \)(,?)/$1 : [$2]$3/g;
	$json =~ s/([^\s]+) => bless\( {([^{}]*)\s*}, 'JS_hash' \)(,?)/$1 : {$2}$3/g;
	$json =~ s/=>/:/g;
	$json =~ s/\s+/ /g;
	return $json;
    }

    sub merge_hashes{
	my $hash1 = shift;
	my $hash2 = shift;
	my $new_hash = {};
	if(!$hash2){
	    return $hash1;
	}
	if(ref($hash1) eq 'JS_array'){
	    $new_hash = bless {}, 'JS_array';
	    foreach my $k (keys %{$hash1}){
		$new_hash->{$k}++;
	    }
	    foreach my $k (keys %{$hash2}){
		$new_hash->{$k}++;
	    }
	    return $new_hash;
	}
	if( ref( $hash1 ) ne "JS_hash" ){
	    if( $hash1 ne $hash2 ){ return "conflict" }
	    else{ return $hash1 }
	}
	$new_hash = bless {}, 'JS_hash';
	foreach my $k (keys %{$hash1}){
	    $new_hash->{$k} = merge_hashes($hash1->{$k}, $hash2->{$k});
	}
	foreach my $k (keys %{$hash2}){
	    if($new_hash->{$k}){ next }
	    $new_hash->{$k} = $hash2->{$k};
	}
	return $new_hash;
    }
    
    sub json_to_hash{
	my $json = shift; # should be like this "{ key : val}"
	$json =~ s/^ *//;
	$json =~ s/ *$//;
	$json =~ s/\n/ /sg;
	$json =~ s/,$//;

	if($json !~ /[{}\[\]]/){ # ie no structure
	    $json =~ s/^ *//;
	    $json =~ s/"//g;
	    return $json;
	}
	if($json =~ /^\[[^\]]+\]$/){ # ie array
	    $json =~ s/"//g;
	    $json =~ s/[\[\]]+//g;
	    my @arr =  split(/,/, $json);
	    my $new_hash_ref = bless {}, 'JS_array';
	    foreach my $e (@arr){ $new_hash_ref->{$e} = 1 }
	    return $new_hash_ref;
	}
	$json =~ s/^ *{ *//;
	$json =~ s/ *}; *$//;
	$json =~ s/ +:/:/g;
	$json =~ s/: +/:/g;
	my $regex;
	$regex = qr/"?([^:]+)"?:([^\[\]{},]+,?|\[[^\]]+\],?|{[^}]+},?)/x;
	my @arr = split($regex, $json);
	shift @arr;	
	foreach my $k(@arr){$k=~s/,$//;}
	my $new_hash_ref = bless {}, 'JS_hash';;
	while(@arr){
	    my $k = shift @arr;
	    my $v = shift @arr;
	    $k =~ s/^ //;
	    $v =~ s/[" ]//g;
	    shift @arr; # empty :-(
	    if($k eq "_"){ next }
	    $new_hash_ref->{$k} = json_to_hash($v);
	}
	return $new_hash_ref;
    }

}
# end of join ----------


if ($action eq 'saveas') {


    my $newname = CGI::param('newname');
    my $new_query_id = time() . "_" . int(rand 100);
    my $query_id = CGI::param('for_saveas');

    my $query_id_path = $hits_dir . "/" . $query_id;

    my @files = <$query_id_path*>;
    foreach my $file (@files) {
	my $nfile = $file;
	$nfile =~ s/$query_id/$new_query_id/;
	copy($file,$nfile);
    }

    my $top = $hits_dir . "/" . $query_id . ".top";
    my $newtop = $hits_dir . "/" . $new_query_id . ".top";
    open (TOP, $top);
    open (NEWTOP, ">$newtop");

    while (<TOP>) {
	s/query_id=$query_id/query_id=$new_query_id/g;
	s/name=[^']+/name=$newname'/;
	print NEWTOP;
    }

    my $conf = $hits_dir . "/" . $query_id . ".conf";
    my $newconf = $hits_dir . "/" . $new_query_id . ".conf";
    open (CONF, $conf);
    open (NEWCONF, ">$newconf");

    while (<CONF>) {
	my ($key,$val) = split(/\s*=\s*/, $_);
	if ($key eq 'name') {
	    print NEWCONF "name = ", $newname, "\n";
	}
	else {
	    print NEWCONF;	    
	}

    }

}






print "<img src='http://omilia.uio.no/img/tri.png' /><br />Due to a bug, results saved prior to 30. March, 2012 may be retrieved incorrectly when using this page.<br />If you experience any problems, contact us at the Text Laboratory.<br /><br />";
print "<form action='$conf{cgiRoot}get_hits.cgi' method='GET'>\n<table border=1>\n";
print "<th>name</th><th>delete</th><th>rename</th><th>copy</th><th>add</th>\n";

print "<input type='hidden' value='join' name='action'></input>\n";
print "<input type='hidden' value='$corpus' name='corpus'></input>\n";

my @confs=();
my @confs = <$hits_dir/*.conf>;

my %nameId = ();

foreach my $conf (@confs) {
    my $query_id = $conf;
    $query_id =~ s/\.conf$//;
    $query_id =~ s/.*\///;

    my $name;
    open (CONF, $conf);
    while (<CONF>) {
        chomp;
        my ($key,$val) = split(/\s*=\s*/, $_);
        if ($key eq "name") {
            $name=$val;
        }
    }
    close CONF;

    next unless $name;
    $nameId{$name} = $query_id;
}

my @myResults = keys %nameId;

@myResults = sort{ lc($a) cmp lc($b) } @myResults;

foreach my $name (@myResults) {

    my $query_id = $nameId{$name};

    print "<tr>\n<td><a href='", $conf{'cgiRoot'}, "/show_page_dev.cgi?query_id=$query_id&name=$name&corpus=$corpus&n=1&player=$player'>$name</a></td>\n";
    print "<td><a href='", $conf{'cgiRoot'}, "/get_hits.cgi?action=delete&for_deletion=$query_id&corpus=$corpus'>*</a></td>\n";
    print "<td>to: <input type='text' id='renameto$name' size=9></input> <a id='rename$name' href='", $conf{'cgiRoot'}, "/get_hits.cgi?action=rename&for_renaming=$query_id&corpus=$corpus' onClick='getNewName(\"$name\",\"rename\")'>*</a></td>\n";

    print "<td>to: <input type='text' id='saveasto$name' size=9></input> <a id='saveas$name' href='", $conf{'cgiRoot'}, "/get_hits.cgi?action=saveas&for_saveas=$query_id&corpus=$corpus' onClick='getNewName(\"$name\",\"saveas\")'>*</a></td>\n";
    
    print "<td><input type='checkbox' name='joinme' value='$query_id'></input></td>\n</tr>\n";
}

print "</table>\n"; 

print "<br>join selected with new name: ";
print "<input name='newname'>\n";

print "<input type='submit' value='join results'></input>\n";

print "</form>\n";
print "</body>\n</html>\n";
