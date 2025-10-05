"""
Management command to fix centroids for all administrative divisions.
Recalculates centroids using point_on_surface instead of geometric centroid
to ensure the point is always inside the polygon (critical for irregular shapes).
"""

from django.core.management.base import BaseCommand
from core.models import AdministrativeDivision


class Command(BaseCommand):
    help = 'Recalculate centroids for all administrative divisions using point_on_surface'

    def add_arguments(self, parser):
        parser.add_argument(
            '--country',
            type=str,
            help='Limit to specific country ISO3 code (e.g., CAN, BEN)',
        )
        parser.add_argument(
            '--level',
            type=int,
            help='Limit to specific admin level (0-5)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        # Build query
        queryset = AdministrativeDivision.objects.filter(
            area_geometry__isnull=False
        )

        if options['country']:
            queryset = queryset.filter(country__iso3=options['country'])
            self.stdout.write(f"Filtering by country: {options['country']}")

        if options['level'] is not None:
            queryset = queryset.filter(admin_level=options['level'])
            self.stdout.write(f"Filtering by level: {options['level']}")

        total = queryset.count()
        self.stdout.write(f"\nFound {total} divisions with area geometry")

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('\n🔍 DRY RUN MODE - No changes will be made\n'))

        updated = 0
        skipped = 0

        for division in queryset.iterator():
            try:
                # Get old centroid for comparison
                old_centroid = division.centroid

                # Calculate new centroid using point_on_surface
                new_centroid = division.area_geometry.point_on_surface

                # Check if they're different
                if old_centroid and new_centroid:
                    # Calculate distance between old and new (in degrees, rough check)
                    distance = ((old_centroid.x - new_centroid.x) ** 2 +
                               (old_centroid.y - new_centroid.y) ** 2) ** 0.5

                    if distance > 0.0001:  # ~11 meters at equator
                        if options['dry_run']:
                            self.stdout.write(
                                f"  Would update: {division.name} "
                                f"(moved {distance:.6f}°)"
                            )
                        else:
                            division.centroid = new_centroid
                            # Use update_fields to avoid triggering full save logic
                            division.save(update_fields=['centroid'])
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"  ✓ Updated: {division.name} "
                                    f"(moved {distance:.6f}°)"
                                )
                            )
                        updated += 1
                    else:
                        skipped += 1
                else:
                    # No old centroid or couldn't calculate - just update
                    if not options['dry_run']:
                        division.centroid = new_centroid
                        division.save(update_fields=['centroid'])
                        self.stdout.write(
                            self.style.SUCCESS(f"  ✓ Set centroid: {division.name}")
                        )
                    updated += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"  ✗ Error processing {division.name}: {e}"
                    )
                )

        # Summary
        self.stdout.write("\n" + "=" * 60)
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN: Would update {updated} centroids, "
                    f"skip {skipped} (no change needed)"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Updated {updated} centroids, "
                    f"skipped {skipped} (no change needed)"
                )
            )
        self.stdout.write("=" * 60 + "\n")
