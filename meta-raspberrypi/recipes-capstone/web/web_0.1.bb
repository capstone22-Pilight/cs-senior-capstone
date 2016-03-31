DESCRIPTION = "Get and unpack the Flask web app"
PR = "r0"
LICENSE= "MIT"
LIC_FILES_CHKSUM = "file://cs-senior-capstone/LICENSE;md5=6a01e8ccc65bea4e8bfa79b09ea1444c"

SRC_URI = "https://github.com/rettigs/cs-senior-capstone"

SRC_URI[md5sum] = "d42594a985f063c065ad7acf06663f9f"
SRC_URI[sha256sum] = "6f7687bef4eedf6d4caf8ef385eed69f5f3f038b10cd3b229145ccd70359c94f"

FILES_${PN} += " \
                /home/root/* \
                "
S = "${WORKDIR}"

DEPENDS_${PN}-dev = ""
ALLOW_EMPTY_${PN} = "1"

do_fetch(){
    rm -rf ${S}/web
    git clone http://github.com/rettigs/cs-senior-capstone ${S}/web
}

do_install(){
    install -d ${D}/home/root/
    cp -r ${WORKDIR}/web ${D}/home/root/
}

do_unpack[noexec]= "1"
