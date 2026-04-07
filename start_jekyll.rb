#!/usr/bin/env ruby

# Force EventMachine to use pure Ruby implementation
ENV['EVENTMACHINE_LIBRARY'] = 'pure_ruby'
require 'em/pure_ruby'

# Run Jekyll
system('bundle exec jekyll serve')
