# SPDX-License-Identifier: BSD-2-Clause
# SPDX-FileCopyrightText: 2021 Nextcloud GmbH and Nextcloud contributors

import os

import info
from Package.CMakePackageBase import *

class subinfo(info.infoclass):
    def registerOptions(self):
        self.options.dynamic.registerOption("devMode", False)
        self.options.dynamic.registerOption("versionSuffix", "")
        self.options.dynamic.registerOption("buildWithWebEngine", True)
        if CraftCore.compiler.isMacOS:
            self.options.dynamic.registerOption("osxArchs", "arm64")
            self.options.dynamic.registerOption("buildMacOSBundle", True)
            self.options.dynamic.registerOption("buildFileProviderModule", False)
            self.options.dynamic.registerOption("sparkleLibPath", "")
            self.options.dynamic.registerOption("overrideServerUrl", "")
            self.options.dynamic.registerOption("forceOverrideServerUrl", False)

    def setTargets(self):
        self.svnTargets["master"] = "[git]https://github.com/dayersvid/vilcanet-nube-desktop"

        self.description = "Vilcanet Nube"
        self.displayName = "Vilcanet Nube"
        self.webpage = "https://vilcanet.com.ec"

        self.defaultTarget = "master"

    def setDependencies(self):
        self.buildDependencies["dev-utils/cmake"] = None
        self.runtimeDependencies["libs/qt6/qtbase"] = None
        self.runtimeDependencies["libs/qt6/qtdeclarative"] = None
        self.runtimeDependencies["libs/qt6/qtwebsockets"] = None
        self.runtimeDependencies["libs/qt/qtsvg"] = None
        self.runtimeDependencies["libs/qt6/qt5compat"] = None
        self.runtimeDependencies["libs/zlib"] = None
        self.runtimeDependencies["libs/libp11"] = None
        self.runtimeDependencies["libs/kdsingleapplication"] = None
        self.runtimeDependencies["qt-libs/qtkeychain"] = None
        self.runtimeDependencies["kde/frameworks/tier1/karchive"] = None
        if CraftCore.compiler.isLinux:
            self.runtimeDependencies["kde/frameworks/tier1/kdbusaddons"] = None
            self.runtimeDependencies["libs/openvfs"] = None

        self.runtimeDependencies["libs/openssl"] = None

class Package(CMakePackageBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        def boolToCmakeBool(value: bool) -> str:
            return "ON" if value else "OFF"

        devMode = self.subinfo.options.dynamic.devMode
        versionSuffix = self.subinfo.options.dynamic.versionSuffix
        overrideServerUrl = self.subinfo.options.dynamic.overrideServerUrl

        # Make sure we do not set the application server url to empty if it is not set, this can
        # unintentionally break our use of NEXTCLOUD.cmake
        if overrideServerUrl:
            forceOverrideServerUrl = "ON" if self.subinfo.options.dynamic.forceOverrideServerUrl == True else "OFF"
            self.subinfo.options.configure.args += [
                f"-DAPPLICATION_SERVER_URL={overrideServerUrl}",
                f"-DAPPLICATION_SERVER_URL_ENFORCE={forceOverrideServerUrl}"
            ]

        if devMode:
            self.subinfo.options.configure.args += [f"-DNEXTCLOUD_DEV=ON"]

        self.subinfo.options.configure.args += [f"-DMIRALL_VERSION_SUFFIX={versionSuffix}"]

        # Contador de compilaciones propio (1 a 65535: limite de Windows por cada parte de la version)
        build = os.environ.get("VILCANET_BUILD", "")
        if build.isdigit() and 1 <= int(build) <= 65535:
            self.subinfo.options.configure.args += [f"-DMIRALL_VERSION_BUILD={build}"]

        if CraftCore.compiler.isMacOS:
            osxArchs = self.subinfo.options.dynamic.osxArchs
            buildAppBundle = boolToCmakeBool(self.subinfo.options.dynamic.buildMacOSBundle)
            buildFileProviderModule = boolToCmakeBool(self.subinfo.options.dynamic.buildFileProviderModule)
            sparkleLibPath = self.subinfo.options.dynamic.sparkleLibPath
            self.subinfo.options.configure.args += [
                f"-DCMAKE_OSX_ARCHITECTURES={osxArchs}",
                f"-DBUILD_OWNCLOUD_OSX_BUNDLE={buildAppBundle}",
                f"-DBUILD_FILE_PROVIDER_MODULE={buildFileProviderModule}",
                f"-DSPARKLE_LIBRARY={sparkleLibPath}",
            ]

    def createPackage(self):
        self.blacklist_file.append(os.path.join(self.packageDir(), 'blacklist.txt'))
        self.defines["appname"] = "vilcanet-nube"
        self.defines["productname"] = "Vilcanet Nube"
        self.defines["company"] = "Vilcanet"
        self.applicationExecutable = "vilcanet-nube"
        # Icono propio del instalador y de «Aplicaciones» (por defecto Craft pone el suyo)
        self.defines["icon"] = os.path.join(self.packageDir(), "vilcanet-nube.ico")
        # Version visible en «Aplicaciones»: la pasa el flujo de compilacion
        version = os.environ.get("VILCANET_VERSION", "")
        if version:
            self.defines["version"] = version

        # Plantilla propia del instalador: en espanol, con la marca y con las extensiones del Explorador
        self.scriptname = os.path.join(self.packageDir(), "vilcanet-nube.nsi")
        self.defines["vilcanet_dir"] = str(self.packageDir())
        # Nombre con el que el programa se anota en el inicio de Windows (APPLICATION_SHORTNAME)
        self.defines["vilcanet_shortname"] = "VilcanetNube"
        # Acceso directo del menu Inicio: Craft solo lo crea si se lo piden aqui
        # (applicationExecutable no lo usa el empaquetador NSIS)
        self.defines["shortcuts"] = [
            {
                "name": "Vilcanet Nube",
                "target": "bin/vilcanet-nube.exe",
                "description": "Vilcanet Nube",
                "workingDirectory": "$INSTDIR\\bin",
            }
        ]

        self.ignoredPackages += ["binary/mysql"]
        if not CraftCore.compiler.isLinux:
            self.ignoredPackages += ["libs/dbus"]

        return super().createPackage()
