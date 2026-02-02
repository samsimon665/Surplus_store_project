document.addEventListener("DOMContentLoaded", function () {

    window.initExactImageCropper = function (config) {

        const input = document.getElementById(config.inputId);
        if (!input) return;

        let cropper = null;
        let activeInput = input;

        // 🔒 STATE FLAG (CRITICAL)
        let isFromCropper = false;

        // Cropper modal elements
        const cropModal = document.getElementById("cropperModal");
        const cropImage = document.getElementById("cropperImage");
        const cropConfirmBtn = document.getElementById("cropConfirm");
        const cropCancelBtn = document.getElementById("cropCancel");

        // Preview elements (may or may not exist)
        const previewContainer = config.previewContainerId
            ? document.getElementById(config.previewContainerId)
            : null;

        const previewImg = config.previewImgId
            ? document.getElementById(config.previewImgId)
            : null;

        const removeBtn = config.removeBtnId
            ? document.getElementById(config.removeBtnId)
            : null;

        const previewModal = document.getElementById("imagePreviewModal");
        const previewModalImg = document.getElementById("imagePreviewModalImg");
        const previewRow = config.previewRowId
            ? document.getElementById(config.previewRowId)
            : null;

        /* =====================================================
           OPEN CROPPER (INTERCEPT FILE SELECT)
           ===================================================== */
        input.addEventListener("change", function (e) {

            // ✅ If change came from cropper → allow preview logic
            if (isFromCropper) {
                isFromCropper = false;
                return;
            }

            // ❌ Block normal preview for raw file selection
            e.stopImmediatePropagation();

            if (!this.files || !this.files[0]) return;

            const file = this.files[0];

            if (!file.type.startsWith("image/")) {
                alert("Please select a valid image file.");
                this.value = "";
                return;
            }

            const reader = new FileReader();
            reader.onload = function () {

                cropImage.src = reader.result;
                cropModal.classList.remove("hidden");

                if (cropper) cropper.destroy();

                cropper = new Cropper(cropImage, {
                    aspectRatio: config.aspectRatio,
                    viewMode: 0,
                    dragMode: "move",
                    autoCropArea: 0.9,
                    background: false,
                    guides: true,
                    center: true,
                    highlight: false,
                    cropBoxMovable: true,
                    cropBoxResizable: true,
                    toggleDragModeOnDblclick: false,
                });
            };

            reader.readAsDataURL(file);

        }, true); // 👈 capture phase (MANDATORY)

        /* =====================================================
           CONFIRM CROP
           ===================================================== */
        cropConfirmBtn.addEventListener("click", function () {

            if (!cropper || !activeInput) return;

            cropper.getCroppedCanvas({
                width: config.width,
                height: config.height,
            }).toBlob(blob => {

                if (!blob) return;

                const croppedFile = new File(
                    [blob],
                    "cropped.jpg",
                    { type: "image/jpeg" }
                );

                const dt = new DataTransfer();
                dt.items.add(croppedFile);
                activeInput.files = dt.files;

                // ✅ Mark next change as safe for preview
                isFromCropper = true;
                activeInput.dispatchEvent(new Event("change"));

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
            activeInput.value = "";
            cropModal.classList.add("hidden");
        });

        /* =====================================================
           BIG IMAGE PREVIEW (OPTIONAL)
           ===================================================== */
        if (previewRow && previewModal && previewModalImg) {
            previewRow.addEventListener("click", function () {
                const src = previewModalImg.dataset.src;
                if (!src) return;
                previewModalImg.src = src;
                previewModal.classList.remove("hidden");
            });

            previewModal.addEventListener("click", function (e) {
                if (e.target === previewModal) {
                    previewModal.classList.add("hidden");
                    previewModalImg.src = "";
                }
            });
        }

        /* =====================================================
           EDIT MODE (EXISTING IMAGE)
           ===================================================== */
        if (window.existingMainImage && previewImg) {
            if (previewContainer) previewContainer.classList.remove("hidden");
            previewImg.src = window.existingMainImage.url;
            if (previewModalImg) {
                previewModalImg.dataset.src = window.existingMainImage.url;
            }
        }
    };

});
