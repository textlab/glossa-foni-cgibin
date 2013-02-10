package Glossa;

use warnings;
use strict;
use Carp;
use CGI qw/:standard/;
use base qw{ Exporter };
use Data::Dumper;
use DBI;
use Log::Log4perl;
use File::Spec

our $VERSION   = '0.1';
our @EXPORT_OK = qw{ readConfig get_conf_file print_token print_token_target create_tid_list get_metadata_feat };

my $local_log_file = 'log.conf';
my $default_log_file = 'log.default.conf';

my $logger = getLogger('Glossa_local');

# Initializes Log4perl singleton and returns 'Glossa' logger
# instance.
#
# Reads the local log config or alternatively the global one. If none
# of these files are present an empty config is loaded.
sub getLogger {
    my($name) = @_;

    if (Log::Log4perl::initialized()) {
        return Log::Log4perl->get_logger($name);
    }
    
    if (-e $local_log_file) {
        Log::Log4perl->init($local_log_file);
    }
    elsif (-e $default_log_file) {
        Log::Log4perl->init($default_log_file);
    }
    else {
        # use empty config
        my $conf = "";
        Log::Log4perl->init(\$conf);
    }

    return Log::Log4perl->get_logger($name);
}

# Trims the passed string of preceding and trailing whitespace
sub trimString {
    my($str) = @_;

    $str =~ s/^\s+//;
    $str =~ s/\s+$//;

    return $str;
}

my $global_config_file = "paths.conf";
my $corpus_config_file = "cgi.conf";

# reads global and corpus configuration file and constructs config hash
sub readConfig {
    my ($corpus) = @_;

    # read main configuration file
    my $conf_path_fn = $global_config_file;
    $logger->info("Reading global configuration file $conf_path_fn");
    
    my %base_conf = readConfigFile($conf_path_fn);

    # read corpus configuration file
    my $conf_corpus_fn = File::Spec->catfile($base_conf{'config_dir'},
                                             $corpus, $corpus_config_file);

    $logger->info("Reading corpus configuration file $conf_corpus_fn");
    my %conf = readConfigFile($conf_corpus_fn);

    foreach my $key (keys %base_conf) {
        $conf{$key} = $base_conf{$key};
    }

    # update configuration with information passed in the http request
    $conf{'base_corpus'}=$corpus;

    return %conf;
}

# reading the main and corpus config files
# returns a hash of the key=value pairs in the file.
sub readConfigFile {
    my ($fn) = @_;

    my %conf;
    open (CONF, $fn) or $logger->warn("File $fn not found");;;
    while ( <CONF> ) {
        chomp;

        my $line = $_;
        $line = trimString($line);

        # skip comments and empty lines
        next if ($line =~ /^\#/);
        next if ($line =~ /^$/);
        
        my ($k,$v)=split(/\s*=\s*/, $line);
        $conf{trimString($k)} = trimString($v);
    }

    close CONF;

    my $entries = (scalar keys %conf);
    $logger->info("Read $entries configuration keys from $fn");

    return %conf;
}

my $multitag_fn = "multitags.dat";

# Reads the multitag file from the corpus set in $conf{'base_corpus'}
# and returns the Hash with it's contents
sub readMultitagFile {
    my (%conf) = @_;
    my $fn = File::Spec->catfile($conf{'config_dir'},
                                 $conf{'base_corpus'},
                                 $multitag_fn);
    my %multitags;

    $logger->info("Reading multitags from $fn");

    open (M, $fn) or $logger->info("File $fn not found");;
    while (<M>) {
        chomp;
        next if (/^#/);
        s/\s*$//;
        my ($a,$b,$c)=split(/\t/);
        next unless ($a and $b and $c);
        $multitags{$a}->{$b}=$c;
    }
    close M;

    my $entries = (scalar keys %multitags);
    $logger->info("Read $entries multitags from $fn");

    return %multitags
}

my $language_dir = "lang";
my $language_filesuf = "dat";

# read the language file based on %conf and returm the Hash
sub readLanguageFile {
    my(%conf) = @_;
    my $fn = File::Spec->catfile($conf{'config_dir'},
                                 $language_dir,
                                 $conf{'lang'} . "." . $language_filesuf);

    my %lang;

    $logger->info("Reading language strings from $fn");

    open (LANG, $fn) or $logger->info("File $fn not found");
    while (<LANG>) {
        chomp;
        s/\s*$//;
        my ($k,$v)=split(/\s*=\s*/);
        $lang{$k}=$v;
    }
    close LANG;

    my $entries = (scalar keys %lang);
    $logger->info("Read $entries strings from $fn");

    return %lang;
}

# create the media player dom elemenents
# for QT or flash player
sub create_media_player_div {
    my ($player, %conf) = @_;

    if ($player eq 'qt') {
        return create_qt_player_div(%conf);
    }
    else {
        return create_flash_player_div(%conf);
    }
}

# create the qt player
sub create_qt_player_div {
    my (%conf) = @_;

    my $media_div = 
        div({id=>'inspector', class=>'inspect'},
            iframe({frameborder=>0, width=>'100%', height=>'100%',
                    id=>'movie_frame'}, ''),
            div({style=>'position: relative; left: 0px; top: 0px; cursor: pointer;',
                 onclick=>"document.getElementById('inspector').style.display='none';"},
                img({alt=>'[x]', src=>"$conf{'htmlRoot'}/html/img/close.png"})));
    $media_div .= br();

    return $media_div;
}

# create html for the flash mediaplayer
sub create_flash_player_div {
    my (%conf) = @_;

    # make sure there is content or empty string in every div tag
    # otherwise CGI will create illegal self-closing div tags
    my $media_div =
        div({id=>'inspector', class=>'inspect'},
            div({id=>'playerpos',
                 style=>"top:0px;left:0px;position:absolute;width:400px;height:300px"},
                div({id=>'player', class=>'video'},
                    'Loading player...')),
            div({id=>'ctrl', class=>'console'},
                div({id=>'holder', class=>'demo'},
                    div({id=>'slider-range'}, ''),
                    div({style=>"float:left;width:24px;position:absolute;left:6px;bottom:3;"},
                        input({id=>'amountl', type=>'text',
                              style=>'border:0; color:#ff2200; font-weight:bold;width:24px;background:#000;'})),
                    div({id=>'play',
                         style=>'float:left;position:absolute;left:194px;width:12px;height:16px;cursor:pointer;border:0px solid #f00;bottom:3;'},
                        img({src=>"$conf{'htmlRoot'}/player/Button-Play-icon.png",
                             style=>'align:bottom;'})),
                    div({style=>'float:right;width:24px;position:absolute;left:378px;bottom:3;'},
                        input({id=>'amountr', type=>'text',
                               style=>'border:0; color:#ff2200; font-weight:bold;background:#000;width:20px;'})))),
            div({id=>'scrollbox'}, ''),
            div({id=>'pops'}, ''));

    $media_div .= div({id=>'timecodes', style=>'z-index: 1;'}, '');

    return $media_div;
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

# processes the CGI params and store themin a hash.
# - strips off []
# - Converts parameter into a tree structure by splitting on _
# TODO pass cgi params hash instead of accessing it directly to allow testing.
sub create_params {
    my $cgi = CGI->new;

    my %cgi_hash;
    my @prms = $cgi->param();

    foreach my $p (@prms) {
        my $p2 = $p;
        $p2 =~ s/\[\]$//;

        my @vals = $cgi->param($p);

        $cgi_hash{$p2}=\@vals;
    }

    my $in = create_cgi_hash(\%cgi_hash);
    my %in = %$in;

    return %in;
}

# This functions converts the cgi input to a hash, based on underscores
# (_) in the parameter names. This is a bit unintuitive, and is a key point
# to grasp.
# FIXME: examples
sub create_cgi_hash {
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
    my $dbh = DBI->connect($dsn, $conf{'db_uname'}, $conf{'db_pwd'},
                           {RaiseError => 1});    

    my $feattable = $feat;
    $feattable =~ s/\..*//;
    $feat =~ s/.*\.//;

    my $sql = "SELECT $feat from $feattable where tid='$tid';";

    my $sth = $dbh->prepare($sql);
    $sth->execute  || die "Error fetching data: $DBI::errstr";
    my ($featval) = $sth->fetchrow_array;

    return $featval;
}

sub create_tid_list {
    my $conf = shift;
    my %conf = %$conf;
    
    my $in = shift;
    my %in = %$in;

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

    # initialize MySQL
    my $dsn = "DBI:mysql:database=$conf{'db_name'};host=$conf{'db_host'}";
    my $dbh = DBI->connect($dsn, $conf{'db_uname'}, $conf{'db_pwd'},
                           {RaiseError => 1});

    my $cats=$in{'meta'}->{'values'};
    my @all_restr;
    my %tables;

    my $sql_query_nl;
    my $subcorpus_string;

    my %from_string;

    while (my ($cat,$vals) = each %$cats) {

        next unless ($vals->[0]);

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

            if ($fr) {
                push @restr_neg, "$sql >= '$fr'";	    
            }
            if ($to) {
                push @restr_neg, "$sql <= '$to'";	   
            }
            $from_string{$tablename}=1;
        } else {
            # MODE: like / not like / check
            foreach my $val (@$vals) {
                $subcorpus_string .= "\t" . $val;

                if ($mode eq 'check') {
                    $mode = '=';
                }

                my $val_restr = "$sql $mode '$val'";

                if ($mode eq 'NOT LIKE') {
                    push @restr_neg, $val_restr;
                } else {
                    push @restr_pos, $val_restr;
                }

                $from_string{$tablename}=1;
            }
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

    $sql_query = "SELECT distinct $select FROM $from" . $sql_query .
        " order by $text_table_name."; 

    my $order_by_column = "startpos";

    # introduce Speech Corpus variable to handle all these exceptions..
    if (defined($conf{'bounds_type'}) and $conf{'bounds_type'} eq 'multiple') {
        $order_by_column = "bounds";
    }

    $sql_query .= $order_by_column.";" ;

    my $dumpstring;
    my @dumpstring_ary;
    my $dumplength;


    my %texts_allowed;

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
        $dumpstring = join("\n", @dumpstring_ary);
    }

    my $dumpfile = $conf{'tmp_dir'} . "/" . $conf{'query_id'} . ".dump";
    open (DUMP, ">$dumpfile");
    # [AN 04.02.08]
    if(defined($dumpstring)){
        print DUMP $dumplength, "\n", $dumpstring;
    }

    # indicate if a subcorpus is created
    my $subcorpus;
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

sub disjoin {
    my $arg = shift;
    my @conds = @$arg;

    if (!@conds){ return "";}

    return "(" . join(" OR ", @conds) .")";

}

sub create_tid_list2 {
    my $conf = shift;
    my %conf = %$conf;
    
    my $in = shift;
    my %in = %$in;
    
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

    # initialize MySQL
    my $dsn = "DBI:mysql:database=$conf{'db_name'};host=$conf{'db_host'}";
    my $dbh = DBI->connect($dsn, $conf{'db_uname'}, $conf{'db_pwd'},
                           {RaiseError => 1});

    my $cats=$in{'meta'}->{'values'};
    my @all_restr;
    my %tables;

    my $sql_query_nl;
    my $subcorpus_string;

    my %from_string;

    while (my ($cat,$vals) = each %$cats) {
        next unless ($vals->[0]);

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
    $sql_query = "SELECT distinct $select FROM $from" . $sql_query .
        " order by $text_table_name.startpos;"; 

    my $dumpstring;
    my @dumpstring_ary;
    my $dumplength;
    

    my %texts_allowed;
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
