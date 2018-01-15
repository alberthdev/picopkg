Picopkg Documentation
======================

Introduction
-------------
Picopkg is a pico-sized package building system - it is a
simple script that is driven by configuration files to simplify
and easily build packages.

To clarify, this means that this does NOT build raw code directly!
Instead, it is a helper to download, extract, and run other packages'
build systems to configure, build, and install them.

Picopkg features include:

  * Automatic dependency handling
  * Ubitiquous build system support
  * Build caching
  * Process logging
  * Simple configuration

What can picopkg be used for? Here are a few examples:

### 3rd Party Package Building
If your application depends on other 3rd party packages, this tool
can link with your build system to help you build those dependencies
for your application to use.

### Environment Setup
If you are looking to set up a testing or development environment,
this tool can help you create a consistent, deployable environment for
you and others to rely on.

### Continuous Integration
If you have many subcomponents in your application, whether they are
internal, external, or 3rd party, this tool can help you build and
test your subcomponents to ensure stability within your code.

Configuration
--------------
Each directory that is relevant to a package should contain
picopkg.yaml.

The file can either define:
 - a list of subpackages for picopkg to find, and/or
 - a configuration set to build a package.

### Subpackage List
A subpackage list defines the subdirectories to search for
other picopkg.yaml. If a picopkg.yaml is not found, an error
will occur to notify the user/developer of the issue.

The subpackage list is defined by the root YAML identifier,
`subpackage`, and is a YAML list type, filled with strings
of subdirectories to search.

Subdirectories are specified relative to the location that
the picopkg.yaml is stored. Although not required, it is
strongly suggested that the subdirectory naming align with
the package IDs.

Finally, an optional `subpackage_name` can be specified to
name the subpackage list being specified. It should be a
short name describing the subpackage(s)' purpose, e.g.
"APP_NAME Dependencies".

Example:

    # OPTIONAL: name the list of subpackages!
    subpackage_name: App Dependencies
    
    subpackage:
        - packagedir1
        - packagedir2
        - sub/folder/pkg1
        - sub/folder/pkg2
        - asdf
    # For subdirectory asdf, package ID is zxcv.
    # It does NOT have to match, but subdirectory name and ID
    # matching is strongly encouraged to keep sanity.

Package Build Configuration
----------------------------
The package build configuration defines the parameters necessary to
download, extract, configure, build, and/or install a package.

This is the precise order of execution:

  * Extract/Download
  * Verify (cycle to next available source option if failed)
  * Configure
  * Build
  * Test
  * Install

A few fields are necessary to kick it off:

  * `id`: a unique, package ID for your package build configuration.
    This ID should be unique within your configuration files, and
    potentially even more unique if your project has the possibility
    of being integrated elsewhere.

  * `name`: the name of your package.

  * `description`: the description of your package - what is it, and
     what does it do?

  * `homepage`: the homepage of your package.

  * `source`: information on where to get the package from.
  
    * `archive`: the archive to extract. If specified, a local archive
      will be checked and used first before attempting a download.
  
    * `url`: URL to download the package from. Currently, only
      HTTP/HTTPS URLs are supported, with future support for
      FTP/SFTP/SSH/GIT.
    
    * `md5`: MD5 checksum to verify the package archive with.
    
    * `sha1`: SHA1 checksum to verify the package archive with.
    
    * `sha256`: SHA256 checksum to verify the package archive with.
    
    * `sha512`: SHA512 checksum to verify the package archive with.
    
    * (FUTURE) `directory`: the directory where the package resides.
      Mutex with `archive` (because you can't guarantee directory
      integrity)?
      
  * `depends`: dependencies that the package requires before being
     built. This is a list of other package IDs, specified as a YAML
     list of strings.
  
  * `settings`: package settings, specific for picopkg:
  
    * `inherit_build_env_from_depends`: whether to inherit the build
      environment from dependencies or not. These include environment
      variables automatically set. By default, this is disabled.
      (FUTURE: another option to influence how environment is preserved,
      e.g. override vs. append, append being the current implementation)
    
  * `config`: configuration commands to execute, in order, specified as
    a YAML list of strings. These commands are for configuring the
    package build, such as running `configure`, `cmake`, etc. to
    generate configuration and build files.

  * `build`: build commands to execute, in order, specified as a YAML
    list of strings. These commands are for actually building the
    package, such as running `make`.

  * `test`: test commands to execute, in order, specified as a YAML
    list of strings. These commands are for testing the build package,
    such as running `make test` or `make check`.

  * `install`: installation commands to execute, in order, specified as
    a YAML list of strings. These commands are for installing the
    built package into a prefix, either for future use by other packages
    or the user.

Example:

    include:
        - dummy.yaml
    pkgs:
        ffms2:
            metadata:
                # Package Metadata
                name: FFmpegSource (FFMS2)
                description: A cross-platform wrapper library around FFmpeg/libav
                homepage: https://github.com/FFMS/ffms2
                source_url: https://github.com/FFMS/ffms2/archive/2.23.tar.gz
                source_folder: ffms2-2.23
            
            # Dependencies
            depends:
                - ffmpeg
                - icu
            
            # Environment:
            env:
                PKG_CONFIG_PATH: {ffmpeg.prefix}/lib/pkgconfig
            
            # Define steps
            actions:
                - download
                - extract
                - prepare:
                    always: true
                - config
                - build
                - install
            
            # Download Definition
            download:
                steps:
                    - picopkg.download:
                        url: {metadata.source_url}
                        set_path_to: persist.saved_archive
                        md5:
                        sha1:
                        sha256:
            
            # Extract Definition
            extract:
                steps:
                    - tar -xvf {metadata.saved_archive}
            
            # Prepare Definition
            prepare:
                steps:
                    - picopkg.make_folder:
                        set_path_to: metadata.prefix
                    - cd {metadata.source_folder}
            
            # Configuration Definition
            config:
                - ./bootstrap.sh --prefix={metadata.prefix} --with-icu={icu.metadata.prefix} --with-ffmpeg={ffmpeg.metadata.prefix}
            
            # Build Definition
            build:
                - ./b2 link=static
            
            # Install Definition
            install:
                - ./b2 link=static install

Internals
----------
Picopkg works by parsing 
