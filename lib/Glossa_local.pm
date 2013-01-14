package Glossa;

use warnings;
use strict;
use Carp;
use CGI;
use base qw{ Exporter };
use Data::Dumper;
use DBI;

open (LOG, ">/var/www/cgi-data/omclog");
print LOG "BEGYNNER GLOSSA.PM\n";

our $VERSION   = '0.1';
our @EXPORT_OK = qw{ readConfigFile getRootURIPath get_conf_file print_token print_token_target create_tid_list get_metadata_feat };

# reading the main and corpus config files
# returns a hash of the key=value pairs in the file.
sub readConfigFile {
    my ($fn) = @_;

    my %conf;
    open (CONF, $fn);
    while ( <CONF> ) {
        chomp;
        next if (/^\#/);
        s/\s*$//;
        my ($k,$v)=split(/\s*=\s*/);
        $conf{$k}=$v;
    }
    close CONF;

    return %conf;
}

sub getRootURIPath {
    my $path = $ENV{REQUEST_URI};
    my @parts = split("/", $path);
    
    return join("/", @parts[2..($#parts-2)]);
}
 
sub get_conf_file {

    my $corpus = shift;
    my $conf_file = shift;

    my %conf;

    unless ($corpus) { $corpus = "test" }

    # read configuration file
    unless ($conf_file) {
	$conf_file = "/hf/foni/tekstlab/glossa-0.7/dat/" . $corpus . "/cgi.conf";
    }


    open (CONF, $conf_file);
    while (<CONF>) {
	chomp;
	next if (/^#/);
	s/\s*$//;
	my ($k,$v)=split(/\s*=\s*/);
	$conf{$k}=$v;
    }
    close CONF;
    
    return \%conf;

}
sub create_cgi_hash0 {
    #FIXED (joel 20071221) uses hash_string to recursively build perl code, then evals it.. or so we thought:-/
    my $cgi_hash=shift;
    my %cgi_hash=%$cgi_hash;
    my %in = ();
    while (my ($prm,$vvv) = each %cgi_hash ) {

        my @vals = @$vvv;

        my @prms=split(/_/, $prm);
        my $hash_string = "\$in".hash_string(\@prms, $vvv);
        eval $hash_string;
    }
    return (\%in);
}
sub hash_string{
    my $array = shift;
    my $val = shift;
    my @arr = @$array;
    my $car;
    my @cdr;

    ($car, @cdr) = @arr;

    my $string = "{$car}";

    if(!@cdr){ return "$string = \\\@vals;"; }

    else{ return $string."->".hash_string(\@cdr, $val);  }

}
sub create_cgi_hash2 {
    my $cgi_hash=shift;
    my %cgi_hash=%$cgi_hash;
    # put form information into a hash
    my %in;
    while (my ($prm,$vvv) = each %cgi_hash ) {

	my @vals = @$vvv;
	
	my @prm=split(/_/, $prm);
	
	# FIXME: do recursively, to allow arbitrary expansion
	if (@prm == 2) {
	    $in{$prm[0]}->{$prm[1]}=\@vals;	    
	}
	elsif (@prm == 3) {
	    $in{$prm[0]}->{$prm[1]}->{$prm[2]}=\@vals;	    
	}
	elsif (@prm == 4) {
	    
		#open (DEBUG, ">>/tmp/glossa_debug.txt");
		#print DEBUG Dumper($prm);
		#close DEBUG;
#	    print "0 $prm[0]<br>";
#	    print "1 $prm[1]<br>";
#	    print "2 $prm[2]<br>";
#	    print "3 $prm[3]<br>";
#	    print join(" ", @vals), "<br>";
#	    print "<br>";
	    $in{$prm[0]}->{$prm[1]}->{$prm[2]}->{$prm[3]}=\@vals;	    
	}
    }
    return (\%in);
}

sub create_cgi_hash3 {

    my $cgi_hash=shift;
    my %cgi_hash=%$cgi_hash;

    # put form information into a hash
    my %in;
    while (my ($prm,$vvv) = each %cgi_hash ) {

	my @vals = @$vvv;
	
	my @prm=split(/_/, $prm);

	my $strip;
	my @rest;

	($strip, @rest) = @prm;
	$in{$prm[0]}=%{hash_tree(\@rest, $vvv)};

    }
    return (\%in);

}

sub create_cgi_hash {

    my $cgi=shift;
    
    my %in;

    my @prms = $cgi->param();
    foreach my $prm (@prms){
	
	my @vals = $cgi->param($prm);
	
	my @prm=split(/_/, $prm);
	
	# FIXME: do recursively, to allow arbitrary expansion
	if (@prm == 2) {
	    $in{$prm[0]}->{$prm[1]}=\@vals;	    
	}
	elsif (@prm == 3) {
	    $in{$prm[0]}->{$prm[1]}->{$prm[2]}=\@vals;	    
	}
	elsif (@prm == 4) {
	    $in{$prm[0]}->{$prm[1]}->{$prm[2]}->{$prm[3]}=\@vals;	    
	}
	
    }

    return (\%in);


}
my $teed;
sub get_metadata_feat {

    my ($feat, $tid, $conf) = @_;
    $teed = $tid;
    my %conf = %$conf;
    my $dsn = "DBI:mysql:database=$conf{'db_name'};host=$conf{'db_host'}";
    my $dbh = DBI->connect($dsn, $conf{'db_uname'}, $conf{'db_pwd'}, {RaiseError => 1});    

    my $feattable = $feat;
    $feattable =~ s/\..*//;
    $feat =~ s/.*\.//;

    my $sql = "SELECT $feat from $feattable where tid='$tid';";

    #open (CHECK, ">/var/www/cgi-bin/glossa/check.txt");
    #print CHECK $sql;
    #close(CHECK);
    print LOG "SQL1: $sql\n";
    my $sth = $dbh->prepare($sql);
    $sth->execute  || die "Error fetching data: $DBI::errstr";
    my ($featval) = $sth->fetchrow_array;
#    next unless $featval;
    return $featval;


}
sub create_tid_list {


    my $conf = shift;                my %conf = %$conf;
    my $in = shift;                  my %in = %$in;
    my $CORPUS = shift;
    
    my $aligned_corpora = shift;
    my %aligned_corpora;
    if ($aligned_corpora) {
	%aligned_corpora = %$aligned_corpora;
    } 
    my %aligned_corpora_opt;
    my $aligned_corpora_opt = shift; 
    if ($aligned_corpora_opt) {
	%aligned_corpora_opt = %$aligned_corpora_opt;
    }

    my $base_corpus = shift;
    
    print LOG "I GLOSSA.PM\n";
    print LOG Dumper(%conf);
    print LOG Dumper(%in);
    print LOG "LUKKER GLOSSA.PM\n";
#    close(LOG);

#    open (CHECK, ">/hf/omilia/site/glossa-0.7/dat/upus/hits/Upus/check.txt");

    # initialize MySQL
#my $dsn = "DBI:mysql:database=glossa;host=omilia.uio.no";
    
#my $dbh = DBI->connect($dsn, "glossa_reader", "tuba");

    my $dsn = "DBI:mysql:database=$conf{'db_name'};host=$conf{'db_host'}";
    my $dbh = DBI->connect($dsn, $conf{'db_uname'}, $conf{'db_pwd'}, {RaiseError => 1});


    my $cats=$in{'meta'}->{'values'};
    my @all_restr;
    my %tables;

    my $sql_query_nl;
    my $subcorpus_string;

    my %from_string;

    while (my ($cat,$vals) = each %$cats) {

	next unless ($vals->[0]);
	#print "C: $cat ", join(" ", @$vals), "<br>";
	
	my ($id, $sql) = split(/::/, $cat); 
	my ($tablename, $colname) = split(/\./, $sql);
	
	my @restr_pos;
	my @restr_neg;

	my $mode = $in{'meta'}->{'mode'}->{$id}->[0];

#	print CHECK "<<MODE: $mode>>\n";

	$subcorpus_string .= $mode . "\t" . $id;



	# MODE: range

	if ($mode eq 'range') {
	    my $fr = $vals->[0];
	    my $to = $vals->[1];

	    if ($fr) {
		push @restr_neg, "$sql >= '$fr'";	    
#		$sql_query_nl .= "$sql more than $fr; ";
	    }
	    if ($to) {
		push @restr_neg, "$sql <= '$to'";	   
#		$sql_query_nl .= "$sql less than $to; "; 
	    }
	    $from_string{$tablename}=1;
	}

	# MODE: like / not like / check
	foreach my $val (@$vals) {
	    
	    #print "VAL: $val<br>";
	    $subcorpus_string .= "\t" . $val;

	    if ($mode eq 'check'){ $mode = '=';  }

	    my $val_restr = "$sql $mode '$val'";

	    if($mode eq 'NOT LIKE'){  push @restr_neg, $val_restr; }
	    else { push @restr_pos, $val_restr; }

	    $from_string{$tablename}=1;
	    
	}
	$subcorpus_string .= "\n";
	
	my $restr = "(";

=start
	my $condy;
	$condy = disjoin( \@restr_pos );
	if ( $condy ){ $condy .= " AND ";  }

	$condy .= " NOT " . disjoin( \@restr_neg );
=cut	
	if (@restr_pos) {
	    my $restr_pos = "(" . join(" OR ", @restr_pos) . ")";
	    $restr .= $restr_pos;
	}
	if (@restr_neg) {
	    my $restr_neg = "(" . join(" AND ", @restr_neg) . ")";
	    if (@restr_pos) {
		$restr .= " AND ";
	    }
	    $restr .= $restr_neg;
	}
	
        $restr .= ")";
#$restr .= $condy . ")";
	next if ($restr eq "()");
	push @all_restr, $restr;


	
    }

    $CORPUS = uc($CORPUS);

    my $text_table_name = $CORPUS . "text";  
    my $author_table_name = $CORPUS . "author"; 
    my $class_table_name = $CORPUS . "class";    

    # language restrictions
    # FIXME: how to generalize this?

    my @lang_restr;

   # LN: Her bør vi tenke oss om. Trenger vi lang_restr for de alignede
   # korpusene?
#    foreach my $corpusname ((keys %aligned_corpora), (keys %aligned_corpora_opt), $base_corpus) {
    foreach my $corpusname ($base_corpus) {
	my ($a,$lang)= split(/_/, $corpusname);
	next unless (($a eq 'OMC3') or ($a eq 'OMC4') or ($a eq 'RUN'));
	if ($lang) {
	    $lang=lc($lang);
	    push @lang_restr, "$text_table_name.lang='$lang'";
	}
    }


    if ($base_corpus eq 'SAMNO_SAMISK') {  
	push @lang_restr, "$text_table_name.lang='sme'";
    }
    if ($base_corpus eq 'SAMNO_NORSK') {  
	push @lang_restr, "$text_table_name.lang='nob'";
    }


    my $lang_restr;
    if (@lang_restr > 0) {
	$lang_restr = " (" . join(" OR ", @lang_restr) . ") ";
    } 
    
    my $select= " $text_table_name.tid,$text_table_name.startpos,$text_table_name.endpos";

    # for UPUS, NOTA etc.
    #if ($conf{'bounds_type'} eq 'multiple') {
    # [AN 08.12.07]
    if (defined($conf{'bounds_type'}) and $conf{'bounds_type'} eq 'multiple') {
        $select= " $text_table_name.tid,$text_table_name.bounds";
    }

    my $join;
    my $from = " $text_table_name";
    foreach my $table (keys %from_string) {
	next if ($table =~ m/text/);
	$select .= "," . $table . ".tid";
	$join .= " AND " . $table . ".tid = $text_table_name.tid";
	$from .= "," . $table;
    }
    

    # [AN 04.02.08]
    #my $sql_query;
    my $sql_query = "";
    if ((@all_restr > 0) or (@lang_restr > 0)) {
	$sql_query = " WHERE " . join(" AND ", @all_restr);
    }
    
    if ($lang_restr) {
	if (@all_restr > 0) {
	    $sql_query .= " AND ";
	}
	$sql_query .= $lang_restr;
    } 
    if ($join) {
	$sql_query .= $join;
    }


# $select & $from & $sql_query are wrong here for speech corpora.
    
    $sql_query = "SELECT distinct $select FROM $from" . $sql_query ." order by $text_table_name."; 

    my $order_by_column = "startpos";

    # introduce Speech Corpus variable to handle all these exceptions..
    if (defined($conf{'bounds_type'}) and $conf{'bounds_type'} eq 'multiple') {
	    
#    if ($CORPUS eq 'UPUS' or $CORPUS eq 'SCANDIASYN' or $CORPUS eq 'NOTA'or $CORPUS eq 'DEMO' or $CORPUS eq 'BIGBROTHER'){ 
	$order_by_column = "bounds";
	#$sql_query .= " order by $text_table_name.startpos;" ;
    }

    $sql_query .= $order_by_column.";" ;
#    print CHECK "\n<<".$sql_query.">>\n";

    my $dumpstring;
    my @dumpstring_ary;
    my $dumplength;
    

    my %texts_allowed;

    #print "SQL: $sql_query<br>";
    print LOG "SQL2: $sql_query\n";
    my $sth = $dbh->prepare($sql_query);
    $sth->execute  || die "Error fetching data: $DBI::errstr";
    while (my ($tid,$s,$e) = $sth->fetchrow_array) {
	$texts_allowed{$tid}=1;

	# for UPUS, NOTA etc.
	#if ($conf{'bounds_type'} eq 'multiple') {
	# [AN 08.12.07]
	if (defined($conf{'bounds_type'}) and 
	    $conf{'bounds_type'} eq 'multiple') {
	    
	    my @bounds = split(/\t/, $s);
	    foreach my $b (@bounds) {
		$b =~ s/-/\t/;
		push @dumpstring_ary, $b;
		$dumplength++;
	    }
	}
	else {
	    unless (defined $s) { $s="" }
	    unless (defined $e) { $e="" }
	    $dumpstring .= $s . "\t" . $e . "\n";
	    $dumplength++;	    
	}

    }

    # for UPUS, NOTA etc.
    #if ($conf{'bounds_type'} eq 'multiple') {
    # [AN 08.07]
    if (defined($conf{'bounds_type'}) and $conf{'bounds_type'} eq 'multiple') {
#	my @dumpstring_ary_sorted = sort { $a <=> $b } @dumpstring_ary;
	$dumpstring = join("\n", @dumpstring_ary);
    }

    my $dumpfile = $conf{'tmp_dir'} . "/" . $conf{'query_id'} . ".dump";
    open (DUMP, ">$dumpfile");
    # [AN 04.02.08]
    if(defined($dumpstring)){
	print DUMP $dumplength, "\n", $dumpstring;
    }
    

    my $subcorpus; # indicate if a subcorpus is created
    if (@all_restr > 0) {
	$subcorpus=1;
    };

    my $conf_file=$conf{'tmp_dir'} . "/" . $conf{'query_id'} . ".conf"; 
    open (CONF, ">$conf_file");
    if ($sql_query) {
	print CONF "texts_allowed=", join(" ", keys %texts_allowed), "\n";
    }
    close CONF;


    return ($subcorpus,$sql_query_nl,\%texts_allowed, $subcorpus_string);
    
}


sub disjoin{
    
#    return "(NOTAtext.age = 17)";

    my $arg = shift;
    my @conds = @$arg;

    if (!@conds){ return "";}

    return "(" . join(" OR ", @conds) .")";

}



sub create_tid_list2 {


    my $conf = shift;                my %conf = %$conf;
    my $in = shift;                  my %in = %$in;
    my $CORPUS = shift;
    
    my $aligned_corpora = shift;
    my %aligned_corpora;
    if ($aligned_corpora) {
	%aligned_corpora = %$aligned_corpora;
    } 
    my %aligned_corpora_opt;
    my $aligned_corpora_opt = shift; 
    if ($aligned_corpora_opt) {
	%aligned_corpora_opt = %$aligned_corpora_opt;
    }

    my $base_corpus = shift;

#    open (CHECK, ">/hf/omilia/site/glossa-0.7/dat/upus/hits/Upus/check.txt");

    # initialize MySQL
#my $dsn = "DBI:mysql:database=glossa;host=omilia.uio.no";

#my $dbh = DBI->connect($dsn, "glossa_reader", "tuba");

    my $dsn = "DBI:mysql:database=$conf{'db_name'};host=$conf{'db_host'}";
    my $dbh = DBI->connect($dsn, $conf{'db_uname'}, $conf{'db_pwd'}, {RaiseError => 1});


    my $cats=$in{'meta'}->{'values'};
    my @all_restr;
    my %tables;

    my $sql_query_nl;
    my $subcorpus_string;

    my %from_string;

    while (my ($cat,$vals) = each %$cats) {

	next unless ($vals->[0]);
	#print "C: $cat ", join(" ", @$vals), "<br>";
	
	my ($id, $sql) = split(/::/, $cat); 
	my ($tablename, $colname) = split(/\./, $sql);
	
	my @restr_pos;
	my @restr_neg;

	my $mode = $in{'meta'}->{'mode'}->{$id}->[0];

	$subcorpus_string .= $mode . "\t" . $id;


	# MODE: range
	if ($mode eq 'range') {
	    my $fr = $vals->[0];
	    my $to = $vals->[1];

	    unless ($fr eq '') {
		$tables{$tablename}=1;
		push @restr_neg, "$sql >= '$fr'";	    
		$sql_query_nl .= "$sql more than $fr; ";
	    }
	    unless ($to eq '') {
		$tables{$tablename}=1;
		push @restr_neg, "$sql <= '$to'";	   
		$sql_query_nl .= "$sql less than $to; "; 
	    }
	    $from_string{$tablename}=1;
	}



	# MODE: like / not like / check
	foreach my $val (@$vals) {
	    
	    $subcorpus_string .= "\t" . $val;

	    if ($mode eq 'LIKE') {
		$tables{$tablename}=1;
		my $val_restr = $sql . " " . $mode . " '" . $val . "'";
		push @restr_pos, $val_restr;
		$sql_query_nl .= "$sql is $val; ";
	    }
	    elsif ($mode eq 'NOT LIKE') {
		$tables{$tablename}=1;
		my $val_restr = $sql . " " . $mode . " '" . $val . "'";
		push @restr_neg, $val_restr;
		$sql_query_nl .= "$sql is not $val; ";
	    }
	    elsif ($mode eq 'check') {
		$tables{$tablename}=1;
		my $val_restr = $sql . " " . "=" . " '" . $val . "'";
		push @restr_pos, $val_restr;
		$sql_query_nl .= "$sql is $val; ";
	    }

	    $from_string{$tablename}=1;
	    
	}
	$subcorpus_string .= "\n";
	
	my $restr = "(";
	
	if (@restr_pos) {
	    my $restr_pos = "(" . join(" OR ", @restr_pos) . ")";
	    $restr .= $restr_pos;
	}
	if (@restr_neg) {
	    my $restr_neg = "(" . join(" AND ", @restr_neg) . ")";
	    if (@restr_pos) {
		$restr .= " AND ";
	    }
	    $restr .= $restr_neg;
	}
	
	$restr .= ")";
	next if ($restr eq "()");
	push @all_restr, $restr;


	
    }

    $CORPUS = uc($CORPUS);

    my $text_table_name = $CORPUS . "text";  
    my $author_table_name = $CORPUS . "author"; 
    my $class_table_name = $CORPUS . "class";    

    # language restrictions
    # FIXME: how to generalize this?

    my @lang_restr;

   # LN: Her bør vi tenke oss om. Trenger vi lang_restr for de alignede
   # korpusene?
#    foreach my $corpusname ((keys %aligned_corpora), (keys %aligned_corpora_opt), $base_corpus) {
    foreach my $corpusname ($base_corpus) {
	my ($a,$lang)= split(/_/, $corpusname);
	next unless (($a eq 'OMC3') or ($a eq 'OMC4'));
	if ($lang) {
	    $lang=lc($lang);
	    push @lang_restr, "$text_table_name.lang='$lang'";
	}
    }


    if ($base_corpus eq 'SAMNO_SAMISK') {  
	push @lang_restr, "$text_table_name.lang='sme'";
    }
    if ($base_corpus eq 'SAMNO_NORSK') {  
	push @lang_restr, "$text_table_name.lang='nob'";
    }


    my $lang_restr;
    if (@lang_restr > 0) {
	$lang_restr = " (" . join(" OR ", @lang_restr) . ") ";
    } 
    
    my $select= " $text_table_name.tid,$text_table_name.startpos,$text_table_name.endpos";

    # for UPUS, NOTA etc.
    #if ($conf{'bounds_type'} eq 'multiple') {
    # [AN 08.12.07]
    if (defined($conf{'bounds_type'}) and $conf{'bounds_type'} eq 'multiple') {
        $select= " $text_table_name.tid,$text_table_name.bounds";
    }


    my $join;
    my $from = " $text_table_name";
    foreach my $table (keys %from_string) {
	next if ($table =~ m/text/);
	$select .= "," . $table . ".tid";
	$join .= " AND " . $table . ".tid = $text_table_name.tid";
	$from .= "," . $table;
    }
    

    
    my $sql_query;
    if ((@all_restr > 0) or (@lang_restr > 0)) {
	$sql_query = " WHERE " . join(" AND ", @all_restr);
    }
    
    if ($lang_restr) {
	if (@all_restr > 0) {
	    $sql_query .= " AND ";
	}
	$sql_query .= $lang_restr;
    } 
    if ($join) {
	$sql_query .= $join;
    }


# $select & $from & $sql_query are wrong here for speech corpora.
    
    $sql_query = "SELECT distinct $select FROM $from" . $sql_query . " order by $text_table_name.startpos;"; 


#    print CHECK "\n<<".$sql_query.">>\n";

    my $dumpstring;
    my @dumpstring_ary;
    my $dumplength;
    

    my %texts_allowed;

#    print "SQL: $sql_query<br>";
   #print LOG "SQL3: $sql_query\n";
    my $sth = $dbh->prepare($sql_query);
    $sth->execute  || die "Error fetching data: $DBI::errstr";
    while (my ($tid,$s,$e) = $sth->fetchrow_array) {
	$texts_allowed{$tid}=1;

	# for UPUS, NOTA etc.
	#if ($conf{'bounds_type'} eq 'multiple') {
	# [AN 08.12.07]
	if (defined($conf{'bounds_type'}) and 
	    $conf{'bounds_type'} eq 'multiple') {
	    
	    my @bounds = split(/\t/, $s);
	    foreach my $b (@bounds) {
		$b =~ s/-/\t/;
		push @dumpstring_ary, $b;
		$dumplength++;
	    }
	}
	else {
	    unless (defined $s) { $s="" }
	    unless (defined $e) { $e="" }
	    $dumpstring .= $s . "\t" . $e . "\n";
	    $dumplength++;	    
	}

    }

    # for UPUS, NOTA etc.
    #if ($conf{'bounds_type'} eq 'multiple') {
    # [AN 08.07]
    if (defined($conf{'bounds_type'}) and $conf{'bounds_type'} eq 'multiple') {
#	my @dumpstring_ary_sorted = sort { $a <=> $b } @dumpstring_ary;
	$dumpstring = join("\n", @dumpstring_ary);
    }

    my $dumpfile = $conf{'tmp_dir'} . "/" . $conf{'query_id'} . ".dump";
    open (DUMP, ">$dumpfile");
    # [AN 14.011.08]
    if(defined($dumpstring)) {
	print DUMP $dumplength, "\n", $dumpstring;
    }

    my $subcorpus; # indicate if a subcorpus is created
    if (@all_restr > 0) {
	$subcorpus=1;
    };

    my $conf_file=$conf{'tmp_dir'} . "/" . $conf{'query_id'} . ".conf"; 
    open (CONF, ">$conf_file");
    if ($sql_query) {
	print CONF "texts_allowed=", join(" ", keys %texts_allowed), "\n";
    }
    close CONF;


    return ($subcorpus,$sql_query_nl,\%texts_allowed, $subcorpus_string);
    
}


sub get_token_freq {

    my $sql = shift;
    my $sql_orig = $sql;
    
    my $conf = shift;
    my %conf = %$conf;
    my $CORPUS = shift;

    my $dsn = "DBI:mysql:database=$conf{'db_name'};host=$conf{'db_host'}";
    my $dbh = DBI->connect($dsn, $conf{'db_uname'}, $conf{'db_pwd'}, {RaiseError => 1});

    # FIXME
    return unless ($CORPUS eq 'bokmal');



    $sql =~ s/\.\*/%/g;
    $sql =~ s/word=/form=/g;
    $sql =~ s/ & / and /g;
    $sql =~ s/ \| / or /g;   
    $sql =~ s/\[//g;
    $sql =~ s/\]//g;
    $sql =~ s/ \%c//g;

    # FIXME
    $sql =~ s/ordkl=/pos=/g;

    $sql = "select freq from BOKMAL_BOKMALlexstat where " . $sql . ";";

    my $total = 0;
    #print LOG "SQL4: $sql\n";
    my $sth = $dbh->prepare($sql);
    $sth->execute  || die "Error fetching data: $DBI::errstr";
    while (my ($freq) = $sth->fetchrow_array) {
	$total += $freq;
    }
    $sql_orig =~ s/^\[//;
    $sql_orig =~ s/^\(//g;
    $sql_orig =~ s/\]$//;
    $sql_orig =~ s/\)$//g;
    $sql_orig =~ s/ \%c//g;

    # [AN 23.07.12]: Dette gir feil frekvenser!
    #return "<b>$sql_orig</b> occurs <B>$total</b> in the corpus<br>";
    return '';

}


1;

__END__

=head1 NAME

Glossa

=head1 VERSION

Version 0.1


=head1 SYNOPSIS


=head1 FUNCTIONS

=head2 get_conf_file()

=head1 AUTHOR

Lars Nygaard, C<< <lars.nygaard@inl.uio.no> >>

=head1 BUGS

=head1 COPYRIGHT & LICENSE

Copyright 2006 Lars Nygaard, all rights reserved.

This program is free software; you can redistribute it and/or modify it
under the same terms as Perl itself.

=cut


