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

    price_per_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price per kilogram"
    )

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

    color = models.CharField(max_length=50, blank=True)
    size = models.CharField(max_length=20, blank=True)

    weight = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        help_text="Weight in KG"
    )

    stock = models.PositiveIntegerField(default=1)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.name} ({self.weight} kg)"


class ProductImage(TimeStampedModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        null=True,
        blank=True
    )

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="images",
        null=True,
        blank=True
    )

    image = models.ImageField(upload_to="products/")

    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        if self.variant:
            return f"Variant Image - {self.variant.id}"
        if self.product:
            return f"Product Image - {self.product.name}"
        return "Unlinked Product Image"
