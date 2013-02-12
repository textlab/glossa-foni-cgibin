my $logger = getLogger('Glossa_local');

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
