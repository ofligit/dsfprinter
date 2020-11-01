# OctoPrint-DSFPrinter

This plugin uses the Duet Software Framework python API to directly connect to the DSF socket.

## Setup

Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
or manually using this URL:

    https://github.com/ofligit/dsfprinter/archive/master.zip

The Duet Software Framework must be running on the same Raspberry Pi as OctoPrint. To make DSF coexist with OctoPrint on the same PI a few changes need to be made. You'll need to
- change the port DSF is running DWC2 to something other than port 80
- move OctoPrint to a different path in Haproxy
- set the default backend to point to DWC2

## Configuration

None so far.
