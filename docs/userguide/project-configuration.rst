.. _project-configuration-label:

Project Configuration
=====================

Currently, JSON and YAML are supported as the base file formats. Since YAML is
arguably easier to read, this documentation focuses on the YAML format.

.. code-block:: yaml

    # Every file needs to contain a header, that provides kas with information
    # about the context of this file.
    header:
      # The `version` entry in the header describes for which configuration
      # format version this file was created for. It is used by kas to figure
      # out if it is compatible with this file. The version is an integer that
      # is increased on every format change.
      version: x
    # The machine as it is written into the `local.conf` of bitbake.
    machine: qemux86-64
    # The distro name as it is written into the `local.conf` of bitbake.
    distro: poky
    repos:
      # This entry includes the repository where the config file is located
      # to the bblayers.conf:
      meta-custom:
      # Here we include a list of layers from the poky repository to the
      # bblayers.conf:
      poky:
        url: "https://git.yoctoproject.org/git/poky"
        commit: 89e6c98d92887913cadf06b2adb97f26cde4849b
        layers:
          meta:
          meta-poky:
          meta-yocto-bsp:

A minimal input file consists out of the ``header``, ``machine``, ``distro``,
and ``repos``.

Additionally, you can add ``bblayers_conf_header`` and ``local_conf_header``
which are strings that are added to the head of the respective files
(``bblayers.conf`` or ``local.conf``):

.. code-block:: yaml

    bblayers_conf_header:
      meta-custom: |
        POKY_BBLAYERS_CONF_VERSION = "2"
        BBPATH = "${TOPDIR}"
        BBFILES ?= ""
    local_conf_header:
      meta-custom: |
        PATCHRESOLVE = "noop"
        CONF_VERSION = "1"
        IMAGE_FSTYPES = "tar"

``meta-custom`` in these examples should be a unique name for this
configuration entries.

We recommend that this unique name is the **same** as the name of the
containing repository/layer to ease cross-project referencing.

In given examples we assume that your configuration file is part of a
``meta-custom`` repository/layer. This way it is possible to overwrite or
append entries in files that include this configuration by naming an entry
the same (overwriting) or using an unused name (appending).

Including in-tree configuration files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It's currently possible to include kas configuration files from the same
repository/layer like this:

.. code-block:: yaml

    header:
      version: x
      includes:
        - base.yml
        - bsp.yml
        - product.yml

The paths to the files in the include list are either absolute, if they start
with a `/`, or relative.

If the path is relative and the configuration file is inside a repository,
then path is relative to the repositories base directory. If the
configuration file is not in a repository, then the path is relative to the
parent directory of the file.

Including configuration files from other repos
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It's also possible to include configuration files from other repos like this:

.. code-block:: yaml

    header:
      version: x
      includes:
        - repo: poky
          file: kas-poky.yml
        - repo: meta-bsp-collection
          file: hw1/kas-hw-bsp1.yml
        - repo: meta-custom
          file: products/product.yml
    repos:
      meta-custom:
      meta-bsp-collection:
        url: "https://www.example.com/git/meta-bsp-collection"
        commit: 3f786850e387550fdab836ed7e6dc881de23001b
        layers:
          # Additional to the layers that are added from this repository
          # in the hw1/kas-hw-bsp1.yml, we add here an additional bsp
          # meta layer:
          meta-custom-bsp:
      poky:
        url: "https://git.yoctoproject.org/git/poky"
        commit: 89e6c98d92887913cadf06b2adb97f26cde4849b
        layers:
          # If `kas-poky.yml` adds the `meta-yocto-bsp` layer and we
          # do not want it in our bblayers for this project, we can
          # overwrite it by setting:
          meta-yocto-bsp: excluded

The files are addressed relative to the git repository path.

The include mechanism collects and merges the content from top to bottom and
depth first. That means that settings in one include file are overwritten
by settings in a latter include file and entries from the last include file can
be overwritten by the current file. While merging all the dictionaries are
merged recursively while preserving the order in which the entries are added to
the dictionary. This means that ``local_conf_header`` entries are added to the
``local.conf`` file in the same order in which they are defined in the
different include files. Note that the order of the configuration file entries
is not preserved within one include file, because the parser creates normal
unordered dictionaries.

Including configuration files via the command line
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When specifying the kas configuration file on the command line, additional
configurations can be included ad-hoc:

    $ kas build kas-base.yml:debug-image.yml:board.yml

This is equivalent to static inclusion from some kas-combined.yml like this:

.. code-block:: yaml

    header:
      version: x
      includes:
        - kas-base.yml
        - debug.image.yml
        - board.yml

Command line inclusion allows one to create configurations on-demand, without
the need to write a kas configuration file for each possible combination.

All configuration files combined via the command line either have to
come from the same repository or have to live outside of any versioning control.
kas will refuse any other combination in order to avoid complications and
configuration flaws that can easily emerge from them.

.. note::
  Git submodules are considered to be part of the main repository. Hence,
  including config files from a submodule is supported. The repository root
  is always the root of the main repository (if under VCS) or the directory
  of the first kas config file otherwise.

Working with lockfiles
~~~~~~~~~~~~~~~~~~~~~~

kas supports the use of lockfiles to pinpoint repositories to exact commit ID
(e.g. SHA-1 refs for git). A lockfile hereby only overrides the commit ID
defined in a kas file. When performing the checkout operation (or any other
operation that performs a checkout), kas checks if a file named
``<filename>.lock.<ext>`` is found next to the currently processed kas file.
If this is found, kas loads this file right after processing the current one.
Note, that this applies to both files on the kas cmdline, as well as included
files.

The following example shows this mechanism for a file ``kas/kas-isar.yml``
and its corresponding lockfile ``kas/kas-isar.lock.yml``.

``kas/kas-isar.yml``:

.. code-block:: yaml

  # [...]
  repos:
    isar:
      url: https://github.com/ilbers/isar.git
      branch: next

``kas/kas-isar.lock.yml``:

.. code-block:: yaml

  header:
    version: 14
  overrides:
    repos:
      isar:
        commit: 0336610df8bb0adce76ef8c5a921c758efed9f45

The ``lock`` plugin provides helpers to simplify the creation and update
of lockfiles. For details, see the plugins documentation: :mod:`kas.plugins.lock`.

Configuration reference
~~~~~~~~~~~~~~~~~~~~~~~

``header``: dict [required]
  The header of every kas configuration file. It contains information about
  the context of the file.

  ``version``: integer [required]
    Lets kas check if it is compatible with this file. See the
    :doc:`configuration format changelog <../format-changelog>` for the
    format history and the latest available version.

  ``includes``: list [optional]
    A list of configuration files this current file is based on. They are
    merged in order they are stated. So a latter one could overwrite
    settings from previous files. The current file can overwrite settings
    from every included file. An item in this list can have one of two types:

    item: string
      The path to a kas configuration file, relative to the repository root
      of the current file.

    item: dict
      If files from other repositories should be included, choose this
      representation.

      ``repo``: string [required]
        The id of the repository where the file is located. The repo
        needs to be defined in the ``repos`` dictionary as ``<repo-id>``.

      ``file``: string [required]
        The path to the file, relative to the root of the specified
        repository.

``build_system``: string [optional]
  Defines the bitbake-based build system. Known build systems are
  ``openembedded`` (or ``oe``) and ``isar``. If set, this restricts the
  search of kas for the init script in the configured repositories to
  ``oe-init-build-env`` or ``isar-init-build-env``, respectively. If
  ``kas-container`` finds this property in the top-level kas configuration
  file (includes are not evaluated), it will automatically select the
  required container image and invocation mode.

``defaults``: dict [optional]
  This key can be used to set default values for various properties.
  This may help you to avoid repeating the same property assignment in
  multiple places if, for example, you wish to use the same branch for
  all repositories.

  ``repos``: dict [optional]
    This key can contain default values for some repository properties.
    If a default value is set for a repository property it may still be
    overridden by setting the same property to a different value in a given
    repository.

    ``branch``: string [optional]
      Sets the default ``branch`` property applied to all repositories that
      do not override this.

    ``tag``: string [optional]
      Sets the default ``tag`` property applied to all repositories that
      do not override this.

    ``patches``: dict [optional]
      This key can contain default values for some repository patch
      properties. If a default value is set for a patch property it may
      still be overridden by setting the same property to a different value
      in a given patch.

      ``repo``: string [optional]
        Sets the default ``repo`` property applied to all repository
        patches that do not override this.

``machine``: string [optional]
  Contains the value of the ``MACHINE`` variable that is written into the
  ``local.conf``. Can be overwritten by the ``KAS_MACHINE`` environment
  variable and defaults to ``qemux86-64``.

``distro``: string [optional]
  Contains the value of the ``DISTRO`` variable that is written into the
  ``local.conf``. Can be overwritten by the ``KAS_DISTRO`` environment
  variable and defaults to ``poky``.

``target``: string [optional] or list [optional]
  Contains the target or a list of targets to build by bitbake. Can be
  overwritten by the ``KAS_TARGET`` environment variable and defaults to
  ``core-image-minimal``. Space is used as a delimiter if multiple targets
  should be specified via the environment variable.
  For targets prefixed with ``multiconfig:`` or ``mc:``, corresponding
  entries are added to the ``BBMULTICONFIG`` in ``local.conf``.

``env``: dict [optional]
  Contains environment variable names with either default values or ``null``.
  These variables are made available to bitbake via
  ``BB_ENV_PASSTHROUGH_ADDITIONS`` (``BB_ENV_EXTRAWHITE`` in older Bitbake
  versions) and can be overwritten by the variables of the environment in
  which kas is started.
  Either a string or nothing (``null``) can be assigned as value.
  The former one serves as a default value whereas the latter one will lead
  to add the variable only to ``BB_ENV_PASSTHROUGH_ADDITIONS`` and not to
  the environment where kas is started. Please note, that ``null`` needs to
  be assigned as the nulltype (e.g. ``MYVAR: null``), not as 'null'.

``task``: string [optional]
  Contains the task to build by bitbake. Can be overwritten by the
  ``KAS_TASK`` environment variable and defaults to ``build``.

``repos``: dict [optional]
  Contains the definitions of all available repos and layers. The layers
  are appended to the ``bblayers.conf`` sorted by the repository name first
  and then by the layer name.

  ``<repo-id>``: dict [optional]
    Contains the definition of a repository and the layers, that should be
    part of the build. If the value is ``None``, the repository, where the
    current configuration file is located is defined as ``<repo-id>`` and
    added as a layer to the build. It is recommended that the ``<repo-id>``
    is related to the containing repository/layer to ease cross-project
    referencing.

    ``name``: string [optional]
      Defines under which name the repository is stored. If its missing
      the ``<repo-id>`` will be used.

    ``url``: string [optional]
      The url of the repository. If this is missing, no version control
      operations are performed.

    ``type``: string [optional]
      The type of version control repository. The default value is ``git``
      and ``hg`` is also supported.

    ``commit``: string [optional]
      The full-length commit ID (all-lowercase, no branch names, no symbolic
      refs, no tags) that should be used. If ``url`` was specified but no
      ``commit``, ``branch`` or ``tag``, the revision you get depends on the
      defaults of the version control system used.

    ``branch``: string or nothing (``null``) [optional]
      The upstream branch that should be tracked. If ``commit`` was
      specified, kas checks that the branch contains the commit. If no
      ``commit`` was specified, the head of the upstream branch is checked out.
      The nothing (``null``) value is used to remove a possible default value.

    ``tag``: string or nothing (``null``)  [optional]
      The tag that should be checked out. If a ``commit`` was specified, kas
      checks that the tag points to this commit. This must not be combined
      with ``branch``. The nothing (``null``) value is used to remove a
      possible default value.

    ``path``: string [optional]
      The path where the repository is stored.
      If the ``url`` and ``path`` is missing, the repository where the
      current configuration file is located is defined.
      If the ``url`` is missing and the path defined, this entry references
      the directory the path points to.
      If the ``url`` as well as the ``path`` is defined, the path is used to
      overwrite the checkout directory, that defaults to ``kas_work_dir``
      + ``repo.name``.
      In case of a relative path name ``kas_work_dir`` is prepended.

    ``layers``: dict [optional]
      Contains the layers from this repository that should be added to the
      ``bblayers.conf``. If this is missing or ``None`` or an empty
      dictionary, the path to the repo itself is added as a layer.
      Additionally, ``.`` is a valid value if the repo itself should be added
      as a layer. This allows combinations:

      .. code-block:: yaml

         repos:
           meta-foo:
             url: https://github.com/bar/meta-foo.git
             path: layers/meta-foo
             branch: master
             layers:
               .:
               contrib:

      This adds both ``layers/meta-foo`` and ``layers/meta-foo/contrib`` from
      the ``meta-foo`` repository to ``bblayers.conf``.

      ``<layer-path>``: enum [optional]
        Adds the layer with ``<layer-path>`` that is relative to the
        repository root directory, to the ``bblayers.conf`` if the value of
        this entry is not in this list: ``['disabled', 'excluded', 'n', 'no',
        '0', 'false']``. This way it is possible to overwrite the inclusion
        of a layer in latter loaded configuration files.

    ``patches``: dict [optional]
      Contains the patches that should be applied to this repo before it is
      used.

      ``<patches-id>``: dict [optional]
        One entry in patches with its specific and unique id. All available
        patch entries are applied in the order of their sorted
        ``<patches-id>``.

        ``repo``: string [required]
          The identifier of the repo where the path of this entry is relative
          to.

        ``path``: string [required]
          The path to one patch file or a quilt formatted patchset directory.

``overrides``: dict [optional]
  This object provides a mechanism to override kas configuration items
  without defining them. By that, only items that already exist are
  overridden. Note, that all entries below this key are reserved for
  auto-generation using kas plugins. Do not manually add entries.

  ``repos``: dict [optional]
    Mapps to the top-level ``repos`` entry.

    ``<repo-id>``: dict [optional]
      Mapps to the ``<repo-id>`` entry.

    ``commit``: string [optional]
      Pinned commit ID which overrides the ``commit`` of the corresponding
      repo.

``bblayers_conf_header``: dict [optional]
  This contains strings that should be added to the ``bblayers.conf`` before
  any layers are included.

  ``<bblayers-conf-id>``: string [optional]
    A string that is added to the ``bblayers.conf``. The entry id
    (``<bblayers-conf-id>``) should be unique if lines should be added and
    can be the same from another included file, if this entry should be
    overwritten. The lines are added to ``bblayers.conf`` in alphabetic order
    of ``<bblayers-conf-id>`` to ensure deterministic generation of config
    files.

``local_conf_header``: dict [optional]
  This contains strings that should be added to the ``local.conf``.

  ``<local-conf-id>``: string [optional]
    A string that is added to the ``local.conf``. It operates in the same way
    as the ``bblayers_conf_header`` entry.

``menu_configuration``: dict [optional]
  This contains user choices for a Kconfig menu of a project. Each variable
  corresponds to a Kconfig configuration variable and can be of the types
  string, boolean or integer. The content of this key is typically
  maintained by the ``kas menu`` plugin in a ``.config.yaml`` file.

``artifacts``: dict [optional]
  This entry describes artifacts which are expected to be present after
  executing the build. Each key-value pair describes an identifier and a
  path relative to the kas build dir, whereby the path can contain wildcards
  like '*'. Unix-style globbing is applied to all paths. In case no artifact
  is found, the build is considered successful, if not stated otherwise by
  the used plugin and mode of operation.

  .. note:: There are no further semantics attached to the identifiers (yet).
            Both the author and the consumer of the artifacts node need to
            agree on the semantics.

  Example:

  .. code-block:: yaml

      artifacts:
        disk-image: path/to/image.*.img
        firmware: path/to/firmware.bin
        swu: path/to/update.swu

``_source_dir``: string [optional]
  This entry is auto-generated by the menu plugin and provides the path to
  the top repo at time of invoking the plugin. It must not be set
  manually and might only be defined in the top-level ``.config.yaml`` file.

``_source_dir_host``: string [optional]
  This entry is auto-generated by the menu plugin when invoking kas via
  the ``kas-container`` script. It provides the absolute path to the top repo
  outside of the container (on the host). This value is only evaluated by the
  ``kas-container`` script. It must not be set manually and might only be
  defined in the top-level ``.config.yaml`` file.

``buildtools``: dict [optional]
  Provides variables to define which buildtools version should be fetched and
  where it is (or will be) installed. At least ``dir`` and ``release`` should be
  set. If the directory pointed by ``dir`` is empty, Kas will try to download
  and install buildtools. If ``dir`` already has buildtools installed, Kas will
  check the ``Distro Version`` line in the version file, and if it doesn't match
  with ``release``, the directory will be cleaned and Kas will download
  buildtools according to ``release``. As for the optional variables, they are
  meant to be used to fetch unofficial (i.e., custom) buildtools. Finally, the
  environment-setup script will run before bitbake, so the whole buildtools
  environment will be available. More information on how to install or generate
  buildtools can be found at: |yp_doc_buildtools|

  ``dir``: string
    The path to buildtools' installation directory.

  ``release``: string
    The buildtools version to be fetched. If the path set by ``dir`` is not
    empty, its buildtools version will be read, and if it doesn't match
    ``release``, the directory will be cleaned and the version set by
    ``release`` will be fetched instead.

  ``base_url``: string [optional]
    This variable represents the URL to be passed to ``wget``, excluding
    buildtools script filename. If this variable is not set, the default value
    will be Yocto's standard sources, using ``release`` variable:
    ``https://downloads.yoctoproject.org/releases/yocto/yocto-{release}/buildtools/``

  ``filename``: string [optional]
    Appended to ``base_url`` to form the whole URL to be passed to ``wget``, if
    set. If not set, Kas will combine the platform architecture and release to
    form the standard script filename:
    ``{arch}-buildtools-extended-nativesdk-standalone-{release}.sh``

  Example:

  .. code-block:: yaml

      buildtools:
        dir: downloads/buildtools
        release: "5.0.5"

  And for unofficial sources:

  .. code-block:: yaml

      buildtools:
        dir: downloads/buildtools
        release: "1.0.0"
        base_url: https://downloads.mysources.com/yocto/buildtools/
        filename: x86_64-buildtools-beta-testing-1.0.0.sh

.. |yp_doc_buildtools| replace:: https://docs.yoctoproject.org/dev/ref-manual/system-requirements.html#downloading-a-pre-built-buildtools-tarball

.. _example-configurations-label:

Example project configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following snippets show minimal but working project configurations for
both OpenEmbedded and ISAR based distributions.

OpenEmbedded
------------

.. literalinclude:: ../../examples/openembedded.yml
  :language: YAML
  :lines: 25-

ISAR
----

.. literalinclude:: ../../examples/isar.yml
  :language: YAML
  :lines: 25-
