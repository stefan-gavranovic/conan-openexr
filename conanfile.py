from conans import ConanFile, CMake, tools
from conans.errors import ConanException
import os


class OpenEXRConan(ConanFile):
    name = "openexr"
    description = "OpenEXR is a high dynamic-range (HDR) image file format developed by Industrial Light & Magic for use in computer imaging applications."
    version = "2.3.0"
    license = "BSD"
    url = "https://github.com/jgsogo/conan-openexr.git"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "namespace_versioning": [True, False], "fPIC": [True, False]}
    default_options = "shared=False", "namespace_versioning=True", "fPIC=True"
    generators = "cmake"
    exports = "FindOpenEXR.cmake"

    # requires = "ilmbase/{version}@jgsogo/testing".format(version=version)

    def config_options(self):
        if self.settings.os == "Windows":
            self.options.remove("fPIC")

    def requirements(self):
        self.requires('zlib/1.2.11@conan/stable')

    def configure(self):
        if "fPIC" in self.options.fields and self.options.shared:
            self.options.fPIC = True

        if self.settings.compiler == 'gcc' and self.settings.compiler.libcxx == 'libstdc++':
            raise ConanException("Compile with stdlib=libstdc++11 using settings.compiler.libcxx")

    def source(self):
        url = "https://github.com/openexr/openexr/archive/v{version}.tar.gz"
        tools.get(url.format(version=self.version))
        tools.replace_in_file(os.path.join('openexr-{}'.format(self.version), 'CMakeLists.txt'),
                              'project(OpenEXR VERSION ${OPENEXR_VERSION})',
                              """project(OpenEXR VERSION ${OPENEXR_VERSION})
include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()
""")

    def build(self):
        cmake = CMake(self)
        cmake.definitions["OPENEXR_BUILD_PYTHON_LIBS"] = False
        cmake.definitions["OPENEXR_BUILD_SHARED"] = self.options.shared
        cmake.definitions["OPENEXR_BUILD_STATIC"] = not bool(self.options.shared)
        cmake.definitions["OPENEXR_NAMESPACE_VERSIONING"] = self.options.namespace_versioning
        cmake.definitions["OPENEXR_ENABLE_TESTS"] = False

        # cmake.definitions["OPENEXR_BUILD_ILMBASE"] = False
        # cmake.definitions["ILMBASE_PACKAGE_PREFIX"] = self.deps_cpp_info["ilmbase"].rootpath

        cmake.configure(source_dir='openexr-{}'.format(self.version))
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        self.copy("FindOpenEXR.cmake", src=".", dst=".")
        self.copy("license*", dst="licenses", src="ilmbase-%s" % self.version, ignore_case=True, keep_path=False)

    def package_info(self):
        parsed_version = self.version.split('.')
        version_suffix = "-%s_%s" % (
        parsed_version[0], parsed_version[1]) if self.options.namespace_versioning else ""
        if not self.options.shared:
            version_suffix += "_s"

        self.cpp_info.includedirs = [os.path.join('include', 'OpenEXR'), ]
        self.cpp_info.libs = ['IlmImf' + version_suffix, 'IlmImfUtil' + version_suffix]

        if self.options.shared and self.settings.os == "Windows":
            self.cpp_info.defines.append("OPENEXR_DLL")

        if not self.settings.os == "Windows":
            self.cpp_info.cppflags = ["-pthread"]
