#!/usr/bin/perl

# Copyright 2016 Christian Woerstenfeld, git@loxberry.woerstenfeld.de
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


##########################################################################
# Modules
##########################################################################

use CGI::Carp qw(fatalsToBrowser);
use CGI qw/:standard/;
use Config::Simple;
use File::HomeDir;
use Data::Dumper;
use Cwd 'abs_path';
use HTML::Entities;
use URI::Escape;
use warnings;
use strict;
no  strict "refs"; # we need it for template system

##########################################################################
# Variables
##########################################################################
our $cfg;
our $plugin_cfg;
our $phrase;
our $namef;
our $value;
our %query;
our $lang;
our $template_title;
our @help;
our $helptext="";
our $installfolder;
our $languagefile;
our $version;
our $saveformdata=0;
our $message;
our $nexturl;
our $do="form";
my  $home = File::HomeDir->my_home;
our $psubfolder;
our $languagefileplugin;
our $phraseplugin;
our %Config;
our @known_urls;
our @url_cfg_data;
our $url_info;
our $url_note;
our $url_id;
our $url_use;
our $url_use_hidden; 
our $url_select="";
our $url_numbers=0;
our @config_params;
our $url_count_id;
our $pluginconfigdir;
our $pluginconfigfile;
our @language_strings;
our $wgetbin;
our $configured_urls="";
our $error=""; 
our $INTERVAL;
##########################################################################
# Read Settings
##########################################################################

print "Content-Type: text/html\n\n"; 

# Version of this script
	$version = "0.1";

# Figure out in which subfolder we are installed
	$psubfolder = abs_path($0);
	$psubfolder =~ s/(.*)\/(.*)\/(.*)$/$2/g;

#Set directories + read LoxBerry config
	$cfg              = new Config::Simple("$home/config/system/general.cfg");
	$installfolder    = $cfg->param("BASE.INSTALLFOLDER");
	$lang             = $cfg->param("BASE.LANG");

#Set directories + read Plugin config
	$pluginconfigdir  = "$home/config/plugins/$psubfolder";
	$pluginconfigfile = "$pluginconfigdir/dyndns_refresher.cfg";
	$plugin_cfg 		= new Config::Simple(syntax => 'ini');
	$plugin_cfg 		= Config::Simple->import_from("$pluginconfigfile", \%Config)  or die Config::Simple->error();

# Go through all the plugin config options
	foreach (sort keys %Config) 
	{
		 # If option is an URL => process it in different way
		 if ( substr($_, 0, 11) eq "default.URL" ) 
		 { 
			  # Split config line into pieces - MAC, dyndnsurl and so on
		 	  @url_cfg_data		 = split /:/, $Config{$_};
	      
	      # Remove spaces from MAC
	      $url_cfg_data[0] =~ s/^\s+|\s+$//g;
	      $url_cfg_data[2] = uri_unescape($url_cfg_data[2]);
	      $url_cfg_data[3] = uri_unescape($url_cfg_data[3]);
	      # Put the current line info into the @known_urls array (URL-ID, Used, URL)
		 		push (@known_urls, [ shift @url_cfg_data, shift @url_cfg_data, shift @url_cfg_data, join(" ", @url_cfg_data)]); 
			  $url_numbers = $url_numbers + 1;
		 }
		 # If option is INTERVAL
		 elsif ( substr($_, 0, 16) eq "default.INTERVAL" ) 
		 {
		 	 $INTERVAL = $Config{"default.INTERVAL"};
		 }
	}

# Everything from URL
	foreach (split(/&/,$ENV{'QUERY_STRING'}))
	{
	  ($namef,$value) = split(/=/,$_,2);
	  $namef =~ tr/+/ /;
	  $namef =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
	  $value =~ tr/+/ /;
	  $value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
	  $query{$namef} = $value;
	}

# Set parameters coming in - get over post
	if ( !$query{'saveformdata'} ) { if ( param('saveformdata') ) { $saveformdata = quotemeta(param('saveformdata')); } else { $saveformdata = 0;      } } else { $saveformdata = quotemeta($query{'saveformdata'}); }
	if ( !$query{'lang'} )         { if ( param('lang')         ) { $lang         = quotemeta(param('lang'));         } else { $lang         = $lang;  } } else { $lang         = quotemeta($query{'lang'});         }
	if ( !$query{'do'} )           { if ( param('do')           ) { $do           = quotemeta(param('do'));           } else { $do           = "form"; } } else { $do           = quotemeta($query{'do'});           }

# Init Language
# Clean up lang variable
	$lang         =~ tr/a-z//cd; 
	$lang         = substr($lang,0,2);
	# If there's no language phrases file for choosed language, use german as default
	if (!-e "$installfolder/templates/system/$lang/language.dat") 
	{
		$lang = "de";
	}

# Read translations / phrases
	$languagefile 			= "$installfolder/templates/system/$lang/language.dat";
	$phrase 						= new Config::Simple($languagefile);
	$languagefileplugin = "$installfolder/templates/plugins/$psubfolder/$lang/language.dat";
	$phraseplugin 			= new Config::Simple($languagefileplugin);
	foreach my $key (keys %{ $phraseplugin->vars() } ) 
	{
		(my $cfg_section,my $cfg_varname) = split(/\./,$key,2);
		push @language_strings, $cfg_varname;
	}
	foreach our $template_string (@language_strings)
	{
		${$template_string} = $phraseplugin->param($template_string);
	}		

# Clean up saveformdata variable
	$saveformdata =~ tr/0-1//cd; 
	$saveformdata = substr($saveformdata,0,1);

##########################################################################
# Main program
##########################################################################

	if ($saveformdata) 
	{
	  &save;
	}
	else 
	{
	  &form;
	}
	exit;

#####################################################
# 
# Subroutines
#
#####################################################

#####################################################
# Form-Sub
#####################################################

	sub form 
	{
		# The page title read from language file + plugin name
		$template_title = $phrase->param("TXT0000") . ": " . $phraseplugin->param("MY_NAME");

		# Print Template header
		&lbheader;
		
		# Parse URLs into template
		for $url_count_id (0 .. $#known_urls)
		{
			# Parse variable url_id into template
			$url_id       = "";
			if (defined($known_urls[$url_count_id]->[0]))
			{
				$url_id     = $known_urls[$url_count_id]->[0];
			}

			# Parse url_use values into template
			$url_use        = "unchecked";
			$url_use_hidden = "off";
			if (defined($known_urls[$url_count_id]->[1]))
			{
				 if ($known_urls[$url_count_id]->[1] eq "on")
				 	{
						$url_use        = "checked";
						$url_use_hidden = "on";
					}
			}
			
			# Parse dyndnsurl values into template
			$url_info = "-";
			if (defined($known_urls[$url_count_id]->[2]))
			{
					$url_info = encode_entities($known_urls[$url_count_id]->[2]);
			}
			$url_note = "-";
			if (defined($known_urls[$url_count_id]->[3]))
			{
				  use MIME::Base64 qw( decode_base64 );
					$url_note =  decode_base64( $known_urls[$url_count_id]->[3] );
			}

			# Parse one line with an URL		 	
			open(F,"$installfolder/templates/plugins/$psubfolder/$lang/url_row.html") || die "Missing template /plugins/$psubfolder/$lang/url_row.html";
		  while (<F>) 
		  {
		     $_ =~ s/<!--\$(.*?)-->/${$1}/g;
				 $url_select .= $_;
		  }
		  close(F);
		  $url_count_id ++;
		}

		# Parse the strings we want
		open(F,"$installfolder/templates/plugins/$psubfolder/$lang/settings.html") || die "Missing template plugins/$psubfolder/$lang/settings.html";
		while (<F>) 
		{
			$_ =~ s/<!--\$(.*?)-->/${$1}/g;
		  print $_;
		}
		close(F);

		# Parse page footer		
		&footer;
		exit;
	}

#####################################################
# Save-Sub
#####################################################

	sub save 
	{
		# Write configuration file
		@config_params 		= param; 
		our $save_config 	= 0;
		$url_count_id 		= 1;
		
		# Delete all existing URLs from config
		for my $url_number (1 .. $url_numbers)
		{
			$plugin_cfg->delete("default.URL$url_number"); 
		}

		# Write all lines into config
		for our $config_id (0 .. $#config_params)
		{
			if ($config_params[$config_id] eq "saveformdata" && param($config_params[$config_id]) eq 1)
			{
				$save_config = 1;
			}
			else
			{
	 			$CGI::LIST_CONTEXT_WARN = 0;
				if (substr($config_params[$config_id],0,7) eq "DYNURL_" )
				{
					if ( substr(uc(param(('dyndnsurl'.$config_params[$config_id]))),0,4) eq "HTTP" ) 
					{ 
						$plugin_cfg->param("default.URL$url_count_id", '"DYNURL_'.$url_count_id.':'.param($config_params[$config_id]).':'.param(('dyndnsurl'.$config_params[$config_id])).':'.param(('dyndnsurlnote'.$config_params[$config_id])).'"');
					}
					elsif ( uri_unescape(param(('dyndnsurl'.$config_params[$config_id]))) eq $phraseplugin->param("TXT_ENTER_URL_HERE")) 
					{
						#ignore entry
					}
					else
					{
						$error = "ERROR_"; 
					}
					$url_count_id ++;
		 		}
		 		elsif ( substr($config_params[$config_id],0,15) eq "INTERVAL" )
		 		{
					$plugin_cfg->param($config_params[$config_id], param($config_params[$config_id]));
					$INTERVAL=param($config_params[$config_id]);
		 		}
 			$CGI::LIST_CONTEXT_WARN = 1;
			}
			$config_id ++;
		}
		if ($save_config eq 1)
		{
			$plugin_cfg->save();
	    unlink ("$installfolder/system/cron/cron.01min/$psubfolder");
	    unlink ("$installfolder/system/cron/cron.03min/$psubfolder");
	    unlink ("$installfolder/system/cron/cron.05min/$psubfolder");
	    unlink ("$installfolder/system/cron/cron.10min/$psubfolder");
	    unlink ("$installfolder/system/cron/cron.15min/$psubfolder");
	    unlink ("$installfolder/system/cron/cron.30min/$psubfolder");
	    unlink ("$installfolder/system/cron/cron.hourly/$psubfolder");
	    unlink ("$installfolder/system/cron/cron.daily/$psubfolder");
		  if ($INTERVAL eq "1") 
		  {
		    system ("ln -s $installfolder/webfrontend/cgi/plugins/$psubfolder/bin/$psubfolder.pl $installfolder/system/cron/cron.01min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.03min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.05min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.10min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.15min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.30min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.hourly/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.daily/$psubfolder");
		  }
		  elsif ($INTERVAL eq "3") 
		  {
		    unlink ("$installfolder/system/cron/cron.01min/$psubfolder");
		    system ("ln -s $installfolder/webfrontend/cgi/plugins/$psubfolder/bin/$psubfolder.pl $installfolder/system/cron/cron.03min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.05min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.10min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.15min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.30min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.hourly/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.daily/$psubfolder");
		  }
		  elsif ($INTERVAL eq "5") 
		  {
		    unlink ("$installfolder/system/cron/cron.01min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.03min/$psubfolder");
		    system ("ln -s $installfolder/webfrontend/cgi/plugins/$psubfolder/bin/$psubfolder.pl $installfolder/system/cron/cron.05min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.10min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.15min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.30min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.hourly/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.daily/$psubfolder");
		  }
		  elsif ($INTERVAL eq "10") 
		  {
		    unlink ("$installfolder/system/cron/cron.01min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.03min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.05min/$psubfolder");
		    system ("ln -s $installfolder/webfrontend/cgi/plugins/$psubfolder/bin/$psubfolder.pl $installfolder/system/cron/cron.10min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.15min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.30min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.hourly/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.daily/$psubfolder");
		  }
		  elsif ($INTERVAL eq "15") 
		  {
		    unlink ("$installfolder/system/cron/cron.01min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.03min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.05min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.10min/$psubfolder");
		    system ("ln -s $installfolder/webfrontend/cgi/plugins/$psubfolder/bin/$psubfolder.pl $installfolder/system/cron/cron.15min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.30min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.hourly/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.daily/$psubfolder");
		  }
		  elsif ($INTERVAL eq "30") 
		  {
		    unlink ("$installfolder/system/cron/cron.01min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.03min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.05min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.10min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.15min/$psubfolder");
		    system ("ln -s $installfolder/webfrontend/cgi/plugins/$psubfolder/bin/$psubfolder.pl $installfolder/system/cron/cron.30min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.hourly/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.daily/$psubfolder");
		  }
		  elsif ($INTERVAL eq "60") 
		  {
		    unlink ("$installfolder/system/cron/cron.01min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.03min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.05min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.10min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.15min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.30min/$psubfolder");
		    system ("ln -s $installfolder/webfrontend/cgi/plugins/$psubfolder/bin/$psubfolder.pl $installfolder/system/cron/cron.hourly/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.daily/$psubfolder");
		  }
		  elsif ($INTERVAL eq "1440") 
		  {
		    unlink ("$installfolder/system/cron/cron.01min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.03min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.05min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.10min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.15min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.30min/$psubfolder");
		    unlink ("$installfolder/system/cron/cron.hourly/$psubfolder");
		    system ("ln -s $installfolder/webfrontend/cgi/plugins/$psubfolder/bin/$psubfolder.pl $installfolder/system/cron/cron.daily/$psubfolder");
		  }
		}
		else
		{
			exit(1);
		}
		$template_title = $phrase->param("TXT0000") . ": " . $phraseplugin->param("MY_NAME");
		$message 				= $phraseplugin->param("TXT_" . $error . "CONFIG_SAVED");
		$nexturl 				= "./index.cgi?do=form";
		
		# Print Template
		&lbheader;
		open(F,"$installfolder/templates/system/$lang/success.html") || die "Missing template system/$lang/succses.html";
		  while (<F>) 
		  {
		    $_ =~ s/<!--\$(.*?)-->/${$1}/g;
		    print $_;
		  }
		close(F);
		&footer;
		exit;
	}

#####################################################
# Error-Sub
#####################################################

	sub error 
	{
		$template_title = $phrase->param("TXT0000") . " - " . $phrase->param("TXT0028");
		
		&lbheader;
		open(F,"$installfolder/templates/system/$lang/error.html") || die "Missing template system/$lang/error.html";
    while (<F>) 
    {
      $_ =~ s/<!--\$(.*?)-->/${$1}/g;
      print $_;
    }
		close(F);
		&footer;
		exit;
	}

#####################################################
# Page-Header-Sub
#####################################################

	sub lbheader 
	{
		 # Create Help page
	  open(F,"$installfolder/templates/plugins/$psubfolder/$lang/help.html") || die "Missing template plugins/$psubfolder/$lang/help.html";
 		  while (<F>) 
		  {
		     $_ =~ s/<!--\$(.*?)-->/${$1}/g;
		     $helptext = $helptext . $_;
		  }

	  close(F);
	  open(F,"$installfolder/templates/system/$lang/header.html") || die "Missing template system/$lang/header.html";
	    while (<F>) 
	    {
	      $_ =~ s/<!--\$(.*?)-->/${$1}/g;
	      print $_;
	    }
	  close(F);
	}

#####################################################
# Footer
#####################################################

	sub footer 
	{
	  open(F,"$installfolder/templates/system/$lang/footer.html") || die "Missing template system/$lang/footer.html";
	    while (<F>) 
	    {
	      $_ =~ s/<!--\$(.*?)-->/${$1}/g;
	      print $_;
	    }
	  close(F);
	}
