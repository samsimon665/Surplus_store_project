from django.db import models

from django.utils.text import slugify

# Create your models here.


#  Abstract base model (NO table created)
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ProductCategory(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Product Category"
        verbose_name_plural = "Product Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1

            while ProductCategory.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)


class SubCategory(TimeStampedModel):
    category = models.ForeignKey(
        ProductCategory, on_delete=models.CASCADE, related_name="subcategories")
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100,  blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/")
    is_active = models.BooleanField(default=True)
    price_per_kg = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Price per KG for this subcategory (surplus pricing)")

    class Meta:
        unique_together = (
            ("category", "name"),
            ("category", "slug"),
        )
        ordering = ["name"]
        verbose_name = "Sub Category"
        verbose_name_plural = "Sub Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.category.name} → {self.name}"


class Product(TimeStampedModel):
    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.CASCADE,
        related_name="products"
    )

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, blank=True)
    description = models.TextField(blank=True)

    # ✅ MAIN PRODUCT IMAGE (CATALOG IMAGE)
    main_image = models.ImageField(
        upload_to="products/main/",
        blank=True,
        null=True,
        help_text="Main product image used in listings & search"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = (
            ("subcategory", "name"),
            ("subcategory", "slug"),
        )

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1

            while Product.objects.filter(
                subcategory=self.subcategory,
                slug=slug
            ).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductVariant(TimeStampedModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants"
    )

    color = models.CharField(max_length=50)
    size = models.CharField(max_length=50)

    weight_kg = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        help_text="Weight of one physical piece in KG"
    )

    stock = models.PositiveIntegerField(default=1)

    is_active = models.BooleanField(default=True)

    # keep SKU optional for now
    sku = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Product Variant"
        verbose_name_plural = "Product Variants"

    def __str__(self):
        return f"{self.product.name} | {self.color} | {self.size}"


class ProductImage(TimeStampedModel):
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="images"
    )

    image = models.ImageField(
        upload_to="products/variants/",
        help_text="Real image of the physical variant"
    )

    is_primary = models.BooleanField(
        default=False,
        help_text="Primary image for this variant/color"
    )

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"

    def __str__(self):
        return f"Variant Image | Variant ID: {self.variant.id}"
