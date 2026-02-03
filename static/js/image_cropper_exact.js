document.addEventListener("DOMContentLoaded", function () {

    /* =====================================================
       EXACT IMAGE CROPPER (STABLE VERSION)
    ===================================================== */

    window.initExactImageCropper = function (config) {

        /* ---------- REQUIRED ELEMENTS ---------- */
        const input = document.getElementById(config.inputId);
        if (!input) {
            console.error("Cropper: input not found");
            return;
        }

        const cropModal = document.getElementById("cropperModal");
        const cropImage = document.getElementById("cropperImage");
        const cropConfirmBtn = document.getElementById("cropConfirm");
        const cropCancelBtn = document.getElementById("cropCancel");

        if (!cropModal || !cropImage || !cropConfirmBtn || !cropCancelBtn) {
            console.error("Cropper modal elements missing");
            return;
        }

        const previewImg = document.getElementById(config.previewImgId);
        const removeBtn = document.getElementById(config.removeBtnId);
        const uploadIcon = document.getElementById("uploadIcon");
        const uploadText = document.getElementById("uploadText");

        let cropper = null;

        /* =====================================================
           FILE SELECT → OPEN CROPPER
        ===================================================== */
        input.addEventListener("change", function () {

            if (!this.files || !this.files[0]) return;

            const file = this.files[0];

            if (!file.type.startsWith("image/")) {
                alert("Please select a valid image");
                input.value = "";
                return;
            }

            const reader = new FileReader();
            reader.onload = function () {

                cropImage.src = reader.result;
                cropModal.classList.remove("hidden");

                if (cropper) cropper.destroy();

                cropper = new Cropper(cropImage, {
                    aspectRatio: config.aspectRatio,   // ✅ SINGLE SOURCE OF TRUTH
                    viewMode: 2,
                    autoCropArea: 0.9,
                    background: false,
                    responsive: true,
                    movable: true,
                    zoomable: true,
                    scalable: false,
                    cropBoxResizable: true,
                    cropBoxMovable: true,
                });



            };

            reader.readAsDataURL(file);
        });

        /* =====================================================
           CONFIRM CROP
        ===================================================== */
        cropConfirmBtn.addEventListener("click", function () {

            if (!cropper) return;

            cropper.getCroppedCanvas({
                width: config.width || 800,
                height: config.height || 800,
                imageSmoothingQuality: "high"
            }).toBlob(function (blob) {

                if (!blob) return;

                const croppedFile = new File(
                    [blob],
                    "cropped.jpg",
                    { type: "image/jpeg" }
                );

                const dt = new DataTransfer();
                dt.items.add(croppedFile);
                input.files = dt.files;

                /* ---------- PREVIEW ---------- */
                if (previewImg) {
                    previewImg.src = URL.createObjectURL(croppedFile);
                    previewImg.classList.remove("hidden");
                }

                if (uploadIcon) uploadIcon.classList.add("hidden");
                if (uploadText) uploadText.classList.add("hidden");

                if (removeBtn) {
                    removeBtn.classList.remove("hidden");
                    removeBtn.onclick = function () {

                        // 1️⃣ Fully reset file input (CRITICAL)
                        input.value = null;
                    
                        // 2️⃣ Kill preview completely
                        if (previewImg) {
                            URL.revokeObjectURL(previewImg.src);
                            previewImg.src = "";
                            previewImg.classList.add("hidden");
                        }
                    
                        // 3️⃣ Restore upload UI
                        if (uploadIcon) uploadIcon.classList.remove("hidden");
                        if (uploadText) uploadText.classList.remove("hidden");
                    
                        // 4️⃣ Hide clear button
                        removeBtn.classList.add("hidden");
                    
                    };
                    
                }

                cropper.destroy();
                cropper = null;
                cropModal.classList.add("hidden");

            }, "image/jpeg", 0.9);
        });

        /* =====================================================
           CANCEL CROP
        ===================================================== */
        cropCancelBtn.addEventListener("click", function () {
            if (cropper) cropper.destroy();
            cropper = null;
            input.value = "";
            cropModal.classList.add("hidden");
        });
    };

    /* =====================================================
       AUTO INIT (DO NOT MOVE)
    ===================================================== */
    initExactImageCropper({
        inputId: "id_image",
        previewImgId: "categoryImagePreview",
        removeBtnId: "clearImageBtn",

        aspectRatio: 4 / 5,   // ✅ FASHION STANDARD
        width: 1000,          // ✅ OUTPUT WIDTH
        height: 1250          // ✅ OUTPUT HEIGHT
    });


});
