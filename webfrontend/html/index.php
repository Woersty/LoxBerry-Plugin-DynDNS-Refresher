<?php
// LoxBerry DynDNS-Refresher Plugin 
// Christian Woerstenfeld - git@loxberry.woerstenfeld.de
// Version 2021.2.11

// Configuration parameters
$temp             = array_filter(explode('/',pathinfo($_SERVER["SCRIPT_FILENAME"],PATHINFO_DIRNAME)));
$psubdir          = array_pop($temp);
$mydir            = pathinfo($_SERVER["SCRIPT_FILENAME"],PATHINFO_DIRNAME);
$plugin_cfg_file  = $mydir."/../../../../config/plugins/$psubdir/dyndns_refresher.cfg";
$general_cfg_file = $mydir."/../../../../config/system/general.cfg";
$logfile          = $mydir."/../../../../log/plugins/$psubdir/dyndns_refresher.log";
$url_prefix       = "DYNURL_";
$json_return      = array();
$urls_known       = array();
$error            = array();
$debug            = 0; // Show update url in logs
    
// Enable logging
ini_set("error_log", $logfile);
ini_set("log_errors", 1);

// Defaults for inexistent variables
if (!isset($_REQUEST["mode"]))        {$_REQUEST["mode"]        = 'normal';}
if (!isset($_SERVER["HTTP_REFERER"])) {$_SERVER["HTTP_REFERER"] = 'direct';}

// Read log and exit
if ($_REQUEST["mode"] == "download_logfile")
{
    if (file_exists($logfile)) 
    {
        error_log( date('Y-m-d H:i:s ')."[LOG] Download logfile [".$_SERVER["HTTP_REFERER"]."]\n", 3, $logfile);
        header('Content-Description: File Transfer');
        header('Content-Type: text/plain');
        header('Content-Disposition: attachment; filename="'.basename($logfile).'"');
        header('Expires: 0');
        header('Cache-Control: must-revalidate');
        header('Pragma: public');
        header('Content-Length: ' . filesize($logfile));
        readfile($logfile);
    }
    else
    {
        error_log( date('Y-m-d H:i:s ')."Error reading logfile! [".$_SERVER["HTTP_REFERER"]."]\n", 3, $logfile);
        die("Error reading logfile."); 
    }
    exit;
}

// Header output
//header('Content-Type: application/json; charset=utf-8');
header('Content-Type: text/html; charset=utf-8');

// Read general config 
foreach(file($general_cfg_file) as $line) 
{
  if(strpos($line, "WGET=") !== false) $cfg_array["BINARIES"]["WGET"] = preg_replace('~[\r\n]+~', '', explode("=",$line)[1]);
}
if (!$cfg_array["BINARIES"]["WGET"]) 
{
    error_log( date('Y-m-d H:i:s ')."Error reading general config! [".$_SERVER["HTTP_REFERER"]."]\n", 3, $logfile);
    die(json_encode(array('error'=>"Error reading general config!",'result'=>"Cannot open general.cfg config file for reading."))); 
}

// Read plugin config 
$plugin_cfg_array = file($plugin_cfg_file);
if (!$plugin_cfg_array) 
{
    error_log( date('Y-m-d H:i:s ')."Error reading plugin config! [".$_SERVER["HTTP_REFERER"]."]\n", 3, $logfile);
    die(json_encode(array('error'=>"Error reading plugin config!",'result'=>"Cannot open plugin config file for reading."))); 
}
// Parse plugin config
foreach($plugin_cfg_array as $line) 
{
    // Add the line to configured_urls-Array, if the value starts with "URL" 
    if (substr($line,0,3) == "URL")
    {
        $configured_urls[]=str_replace('"', '', $line);
    }
}

// Go through all configured urls
if (isset($configured_urls))
{
    if ( !isset( $cfg_array["BINARIES"]["WGET"] ) )
    {
        error_log( date('Y-m-d H:i:s ')."Error reading wget path from general config! [".$_SERVER["HTTP_REFERER"]."]\n", 3, $logfile);
        die(json_encode(array('error'=>"Error reading wget path from general config!",'result'=>"BINARIES.WGET not found."))); 
    }
    else
    {
        $wget  = $cfg_array["BINARIES"]["WGET"] . " -t 1 -T 10 -O /dev/null ";
    }
    while(list($configured_urls_url_key,$configured_urls_url_data) = each($configured_urls))
      {
          $current_url                              = count($urls_known);
          $url_data_line                            = explode("=",$configured_urls_url_data);
          $url_data_array                           = explode(":",$url_data_line[1]);
          if (isset($url_data_array[0]))             { $urls_known["URL$current_url"]['id']      = trim($url_data_array[0]); }
          if (isset($url_data_array[1]))             { $urls_known["URL$current_url"]['use']     = trim($url_data_array[1]); }
          if (isset($url_data_array[2]))             { $urls_known["URL$current_url"]['url']     = urldecode(trim($url_data_array[2])); }
          if (isset($url_data_array[3]))             { $urls_known["URL$current_url"]['name']    = base64_decode(trim($url_data_array[3])); }
            
            // If URL is checked, process it
            if ($urls_known["URL".$current_url]['use'] == "on")
            {
                if ( !isset( $urls_known["URL$current_url"]['url'] ) )
                {
                    error_log( date('Y-m-d H:i:s ')."Error, no URL for ".$urls_known["URL$current_url"]['name']."! [".$_SERVER["HTTP_REFERER"]."]\n", 3, $logfile);
                    $urls_known["URL$current_url"]['error'] = '-1';
                }
                else
                {
                    exec($wget ." '".$urls_known["URL$current_url"]['url']."' >/dev/stdout 2>&1 ",$last_line,$retval);
                    $last_line = array_pop($last_line);
                    if (!$debug) $urls_known["URL$current_url"]['url'] = '-protected-';
                    if ($retval <> 0)
                    {
                        error_log( date('Y-m-d H:i:s ')."[Error] No update of ".$urls_known["URL$current_url"]['name']." with URL ".$urls_known["URL$current_url"]['url']."! Error: $last_line [".$_SERVER["HTTP_REFERER"]."]\n", 3, $logfile);
                        $urls_known["URL$current_url"]['error'] = $last_line;
                    }
                    else
                    { 
                        error_log( date('Y-m-d H:i:s ')."[OK] Successful update of ".$urls_known["URL$current_url"]['name']." with URL ".$urls_known["URL$current_url"]['url']." [".$_SERVER["HTTP_REFERER"]."]\n", 3, $logfile);
                    }
                }
            }
        }
    }
$json_return = $urls_known;
echo json_encode(array_values($json_return));
