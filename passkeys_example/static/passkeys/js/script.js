
(function () {
    let chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_';

    // Use a lookup table to find the index.
    let lookup = new Uint8Array(256);
    for (let i = 0; i < chars.length; i++) {
        lookup[chars.charCodeAt(i)] = i;
    }

    let base64urlencode = function (bytes) {
        const arrayBuf = ArrayBuffer.isView(bytes) ? bytes : new Uint8Array(bytes);
        const binString = Array.from(arrayBuf, (x) => String.fromCodePoint(x)).join("");
        return btoa(binString).replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
    };

    let base64urldecode = function (base64) {
        const padding = "====".substring(base64.length % 4);
        const binString = atob(base64.replaceAll("-", "+").replaceAll("_", "/") + (padding.length < 4 ? padding : ""));
        return Uint8Array.from(binString, (m) => m.codePointAt(0));
    }

    let credToJSON = (pubKeyCred) => {
        let res;
        if (pubKeyCred instanceof Array) {
            res = [];
            for (let i of pubKeyCred)
                res.push(credToJSON(i));

            return res
        }
        if (pubKeyCred instanceof ArrayBuffer) {
            res = base64urldecode(pubKeyCred);
            return res
        }
        if (pubKeyCred instanceof Object) {
            let res = {};

            for (let key in pubKeyCred) {
                res[key] = credToJSON(pubKeyCred[key])
            }

            return res
        }
        console.log(res)
        return pubKeyCred
    }


    let getAssertReq = (getAssert) => {
        getAssert.publicKey.challenge = base64urldecode(getAssert.publicKey.challenge);

        for (let allowCred of getAssert.publicKey.allowCredentials) {
            allowCred.id = base64urldecode(allowCred.id);
        }

        return getAssert
    }


    let startAuthn = function (form, conditionalUI = false) {
        fetch(window.passkeysConfig.urls.authBegin, {
            method: 'GET',
        }).then(function (response) {
            if (response.ok) {
                return response.json().then(function (req) {
                    return getAssertReq(req)
                });
            }
            throw new Error('No credential available to authenticate!');
        }).then(function (options) {
            if (conditionalUI) {
                options.mediation = 'conditional';
                options.signal = window.conditionUIAbortSignal;
            }
            else
                window.conditionUIAbortController.abort()
            res = navigator.credentials.get(options)
            return res;
        }).then(function (assertion) {
            pk = document.querySelector("#passkeys")
            if (pk.length == 0) {
                console.error("Did you add the 'passkeys' hidden input field")
                return
            }
            pk.value = JSON.stringify(credToJSON(assertion));
            console.log(pk.value);
            form = document.getElementById(form.id)
            if (form === null || form === undefined) {
                console.error("Did you pass the correct form id to auth function")
                return;
            }
            form.submit()

        });
        document.addEventListener("DOMContentLoaded", () => {
            if (window.location.protocol != 'https:') {
                console.error("Passkeys must work under secure context")
            }
        });
    }

    function makeCredReq(creds) {
        console.log("CREDS1", creds)

        creds.publicKey.challenge = djangoPasskey.base64urldecode(creds.publicKey.challenge);
        creds.publicKey.user.id = djangoPasskey.base64urldecode(creds.publicKey.user.id);

        for (let excludeCred of creds.publicKey.excludeCredentials) {
            excludeCred.id = djangoPasskey.base64urldecode(excludeCred.id);
        }
        console.log("CREDS", creds)

        return creds
    }

    function beginReg() {
        fetch(window.passkeysConfig.urls.regBegin, {}).then(function (response) {
            if (response.ok) {
                return response.json().then(function (req) {
                    return makeCredReq(req)
                });
            }
            throw new Error('Error getting registration data!');
        }).then(function (options) {

            console.log("options", options)
            return navigator.credentials.create(options);
        }).then(function (attestation) {
            attestation["key_name"] = document.querySelector("#key_name").value;
            attestation["rawId"] = djangoPasskey.base64urlencode(attestation["rawId"])
            for (key in attestation["response"]) {
                attestation["response"][key] = djangoPasskey.base64urlencode(attestation.response.key);
            }
            return fetch(window.passkeysConfig.urls.regComplete, {
                method: 'POST',
                body: JSON.stringify(credToJSON(attestation))
            });
        }).then(function (response) {

            var stat = response.ok ? 'successful' : 'unsuccessful';
            return response.json()
        }).then(function (res) {
            if (res["status"] == 'OK')
                document.querySelector("#res").insertAdjacentHTML("afterbegin", `<div class='alert alert-success'>Registered Successfully, <a href='${window.passkeysConfig.homeURL}'> Refresh</a></div>`)
            else
                document.querySelector("#res").insertAdjacentHTML("afterbegin", "<div class='alert alert-danger'>Registration Failed as " + res + ", <a href='javascript:void(0)' onclick='djangoPasskey.beginReg()'> try again </a> </div>")


        }, function (reason) {
            document.querySelector("#res").insertAdjacentHTML("afterbegin", "<div class='alert alert-danger'>Registration Failed as sdasd " + reason + ", <a href='javascript:void(0)' onclick='djangoPasskey.beginReg()'> try again </a> </div>")
        })
    }




    let methods = {
        'base64urldecode': base64urldecode,
        'base64urlencode': base64urlencode,
        'credToJson': credToJSON,
        "getAssertReq": getAssertReq,
        "startAuthn": startAuthn,
        "makeCredReq": makeCredReq,
        "beginReg": beginReg,
    }

    /**
     * Exporting and stuff
     */
    if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
        module.exports = methods;

    } else {
        if (typeof define === 'function' && define.amd) {
            define([], function () {
                return methods
            });
        } else {
            window.djangoPasskey = methods;
        }
    }
})()

window.conditionalUI = false;
window.conditionUIAbortController = new AbortController();
window.conditionUIAbortSignal = conditionUIAbortController.signal;


function authn(form) {
    djangoPasskey.startAuthn(form, false)
}




function confirmDel(id) {
    $.ajax({
        url: window.passkeysConfig.urls.delKey,
        data: { "id": id },
        success: function (data) {
            alert(data)
            window.location = window.passkeysConfig.urls.home;
        }
    })
}

function start() {
    $("#modal-title").html("Enter a token name")
    $("#modal-body").html(`<p>Please enter a name for your new token</p>
                            <input type="text" placeholder="e.g Laptop, PC" id="key_name" class="form-control"/><br/>
                            <div id="res"></div>
                            `)
    $("#actionBtn").remove();
    $("#modal-footer").prepend(`<button id='actionBtn' class='btn btn-success' onclick="djangoPasskey.beginReg()">Start</button>`)
    $("#popUpModal").show();
}
function deleteKey(id, name) {
    $("#modal-title").html("Confirm Delete")
    $("#modal-body").html("Are you sure you want to delete '" + name + "'? you may lose access to your system if this your only 2FA.");
    $("#actionBtn").remove()
    $("#modal-footer").prepend("<button id='actionBtn' class='btn btn-danger' onclick='confirmDel(" + id + ")'>Confirm Deletion</button>")
    $("#popUpModal").modal('show')
}

function toggleKey(id) {
    $.ajax({
        url: `${window.passkeysConfig.urls.toggle}?id=${id}`,
        success: function (data) {
            if (data == "Error")
                $("#toggle_" + id).toggle()

        },
        error: function (data) {
            $("#toggle_" + id).toggle()
        }
    })
}

if (window.passkeysConfig.enroll) {
    $(document).ready(start)
}
