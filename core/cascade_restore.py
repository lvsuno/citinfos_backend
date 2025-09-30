"""
Enhanced Cascading Restoration System for Django Models

This system properly handles cascading restoration by:
1. Analyzing foreign key relationships automatically
2. Restoring parent objects before child objects
3. Following the inverse order of cascade deletion
4. Using Django's built-in relationship introspection
"""

from django.db import models, transaction
from django.apps import apps
from django.utils import timezone
from collections import defaultdict, deque


class CascadeRestoreAnalyzer:
    """Analyzes model relationships and creates restoration dependency graph."""

    def __init__(self):
        self.dependency_graph = defaultdict(list)
        self.reverse_graph = defaultdict(list)
        self.models_with_soft_delete = set()

    def analyze_relationships(self):
        """Analyze all model relationships and build dependency graphs."""
        self.models_with_soft_delete.clear()
        self.dependency_graph.clear()
        self.reverse_graph.clear()

        # Find all models with soft delete capability
        for app_config in apps.get_app_configs():
            for model in app_config.get_models():
                if self._has_soft_delete(model):
                    self.models_with_soft_delete.add(model)

        # Build dependency graph based on foreign key relationships
        for model in self.models_with_soft_delete:
            self._analyze_model_dependencies(model)

    def _has_soft_delete(self, model):
        """Check if model has soft delete capability."""
        return (
            hasattr(model, 'is_deleted') and
            hasattr(model, 'deleted_at') and
            hasattr(model, 'is_restored') and
            hasattr(model, 'restored_at') and
            hasattr(model, 'last_deletion_at')
        )

    def _analyze_model_dependencies(self, model):
        """Analyze dependencies for a single model."""
        for field in model._meta.get_fields():
            if isinstance(field, models.ForeignKey):
                # This model depends on the foreign key target
                target_model = field.related_model

                # Only consider models with soft delete
                if target_model in self.models_with_soft_delete:
                    # For restoration: target_model must be restored before model
                    self.dependency_graph[target_model].append(model)
                    self.reverse_graph[model].append(target_model)

    def get_restoration_order(self):
        """
        Get the correct order for restoration (topological sort).
        Parents should be restored before children.
        """
        # Use topological sort to determine restoration order
        in_degree = defaultdict(int)

        # Calculate in-degrees
        for model in self.models_with_soft_delete:
            in_degree[model] = len(self.reverse_graph[model])

        # Topological sort
        queue = deque()
        result = []

        # Start with models that have no dependencies (in-degree 0)
        for model in self.models_with_soft_delete:
            if in_degree[model] == 0:
                queue.append(model)

        while queue:
            current_model = queue.popleft()
            result.append(current_model)

            # Process all models that depend on current_model
            for dependent_model in self.dependency_graph[current_model]:
                in_degree[dependent_model] -= 1
                if in_degree[dependent_model] == 0:
                    queue.append(dependent_model)

        # Check for circular dependencies
        if len(result) != len(self.models_with_soft_delete):
            remaining_models = self.models_with_soft_delete - set(result)
            print(f"Warning: Circular dependencies detected in models: {remaining_models}")
            result.extend(remaining_models)  # Add remaining models

        return result

    def get_dependent_objects(self, instance):
        """
        Get all objects that depend on this instance (children that should be restored).
        """
        dependent_objects = []

        for field in instance._meta.get_fields():
            if field.is_relation and hasattr(field, 'get_accessor_name'):
                try:
                    # Get the reverse relationship manager
                    related_manager = getattr(instance, field.get_accessor_name())

                    if hasattr(related_manager, 'filter'):
                        # Find soft-deleted related objects
                        deleted_related = related_manager.filter(is_deleted=True)
                        dependent_objects.extend(deleted_related)

                except (AttributeError, Exception):
                    continue

        return dependent_objects

    def get_dependency_parents(self, instance):
        """
        Get all objects that this instance depends on (parents that should be restored first).
        """
        parent_objects = []

        for field in instance._meta.get_fields():
            if isinstance(field, models.ForeignKey):
                try:
                    parent_obj = getattr(instance, field.name)
                    if parent_obj and hasattr(parent_obj, 'is_deleted') and parent_obj.is_deleted:
                        parent_objects.append(parent_obj)
                except (AttributeError, Exception):
                    continue

        return parent_objects


class EnhancedCascadeRestore:
    """Enhanced cascading restoration with proper dependency handling."""

    def __init__(self):
        self.analyzer = CascadeRestoreAnalyzer()
        self.restoration_stats = {
            'total_restored': 0,
            'models_processed': defaultdict(int),
            'errors': []
        }

    def restore_instance_with_cascade(self, instance, dry_run=False):
        """
        Restore an instance with proper cascading restoration.
        Parents are restored before children.
        """
        if not hasattr(instance, 'is_deleted') or not instance.is_deleted:
            return False, f"{instance.__class__.__name__} is not soft-deleted"

        self.restoration_stats = {
            'total_restored': 0,
            'models_processed': defaultdict(int),
            'errors': []
        }

        if dry_run:
            return self._simulate_cascade_restore(instance)

        try:
            with transaction.atomic():
                return self._perform_cascade_restore(instance)
        except Exception as e:
            error_msg = f"Error during cascading restoration: {str(e)}"
            self.restoration_stats['errors'].append(error_msg)
            return False, error_msg

    def _simulate_cascade_restore(self, instance):
        """Simulate cascading restoration without making changes."""
        restore_plan = []

        # First, restore dependency parents
        parents = self.analyzer.get_dependency_parents(instance)
        for parent in parents:
            restore_plan.append(f"Would restore parent: {parent}")

        # Then restore the instance itself
        restore_plan.append(f"Would restore instance: {instance}")

        # Finally, restore dependent children
        children = self.analyzer.get_dependent_objects(instance)
        for child in children:
            restore_plan.append(f"Would restore child: {child}")

        total_objects = len(parents) + 1 + len(children)
        plan_summary = "\\n".join(restore_plan)

        return True, f"Restoration Plan ({total_objects} objects):\\n{plan_summary}"

    def _perform_cascade_restore(self, instance):
        """Actually perform the cascading restoration."""
        restored_objects = []

        # Step 1: Restore dependency parents first
        parents = self.analyzer.get_dependency_parents(instance)
        for parent in parents:
            if self._restore_single_instance(parent):
                restored_objects.append(parent)

        # Step 2: Restore the main instance
        if self._restore_single_instance(instance):
            restored_objects.append(instance)
        else:
            return False, f"Failed to restore main instance: {instance}"

        # Step 3: Restore dependent children
        children = self.analyzer.get_dependent_objects(instance)
        for child in children:
            if self._restore_single_instance(child):
                restored_objects.append(child)

        self.restoration_stats['total_restored'] = len(restored_objects)

        return True, f"Successfully restored {len(restored_objects)} objects in cascade"

    def _restore_single_instance(self, instance):
        """Restore a single instance."""
        try:
            if not instance.is_deleted:
                return True  # Already restored

            # Store deletion timestamp
            instance.last_deletion_at = instance.deleted_at

            # Restore the instance
            instance.is_deleted = False
            instance.deleted_at = None
            instance.is_restored = True
            instance.restored_at = timezone.now()

            instance.save(update_fields=[
                'is_deleted', 'deleted_at', 'is_restored',
                'restored_at', 'last_deletion_at'
            ])

            model_name = instance.__class__.__name__
            self.restoration_stats['models_processed'][model_name] += 1

            return True

        except Exception as e:
            error_msg = f"Error restoring {instance}: {str(e)}"
            self.restoration_stats['errors'].append(error_msg)
            return False

    def bulk_restore_by_model_order(self, dry_run=False):
        """
        Restore all soft-deleted objects following proper dependency order.
        """
        self.analyzer.analyze_relationships()
        restoration_order = self.analyzer.get_restoration_order()

        if dry_run:
            return self._simulate_bulk_restore(restoration_order)

        try:
            with transaction.atomic():
                return self._perform_bulk_restore(restoration_order)
        except Exception as e:
            error_msg = f"Error during bulk restoration: {str(e)}"
            return False, error_msg

    def _simulate_bulk_restore(self, restoration_order):
        """Simulate bulk restoration."""
        simulation_plan = []
        total_objects = 0

        for model in restoration_order:
            deleted_count = model.objects.filter(is_deleted=True).count()
            if deleted_count > 0:
                simulation_plan.append(
                    f"Would restore {deleted_count} {model.__name__} objects"
                )
                total_objects += deleted_count

        plan_summary = "\\n".join(simulation_plan)
        return True, f"Bulk Restoration Plan ({total_objects} total objects):\\n{plan_summary}"

    def _perform_bulk_restore(self, restoration_order):
        """Perform bulk restoration following dependency order."""
        total_restored = 0

        for model in restoration_order:
            deleted_objects = model.objects.filter(is_deleted=True)

            for obj in deleted_objects:
                if self._restore_single_instance(obj):
                    total_restored += 1

        self.restoration_stats['total_restored'] = total_restored

        return True, f"Successfully restored {total_restored} objects across all models"


# Add methods to SoftDeleteModel
def add_cascade_restore_methods():
    """Add enhanced cascade restore methods to SoftDeleteModel."""

    def restore_instance(self, cascade=True, dry_run=False):
        """Enhanced restoration with proper cascading."""
        if cascade:
            restorer = EnhancedCascadeRestore()
            return restorer.restore_instance_with_cascade(self, dry_run=dry_run)
        else:
            # Simple restoration without cascade
            if not self.is_deleted:
                return False, f"{self.__class__.__name__} is not deleted"

            self.last_deletion_at = self.deleted_at
            self.is_deleted = False
            self.deleted_at = None
            self.is_restored = True
            self.restored_at = timezone.now()

            self.save(update_fields=[
                'is_deleted', 'deleted_at', 'is_restored',
                'restored_at', 'last_deletion_at'
            ])

            return True, f"{self.__class__.__name__} restored successfully"

    @classmethod
    def bulk_cascade_restore(cls, queryset=None, dry_run=False):
        """Bulk restoration with proper dependency handling."""
        restorer = EnhancedCascadeRestore()

        if queryset is None:
            # Restore all objects following dependency order
            return restorer.bulk_restore_by_model_order(dry_run=dry_run)
        else:
            # Restore specific queryset objects
            total_restored = 0
            errors = []

            for obj in queryset.filter(is_deleted=True):
                try:
                    success, message = restorer.restore_instance_with_cascade(obj, dry_run=dry_run)
                    if success and not dry_run:
                        total_restored += 1
                except Exception as e:
                    errors.append(f"Error restoring {obj}: {str(e)}")

            if errors:
                return False, f"Restored {total_restored} objects with {len(errors)} errors"
            return True, f"Successfully restored {total_restored} objects"

    def get_restoration_dependencies(self):
        """Get restoration dependency information for this instance."""
        analyzer = CascadeRestoreAnalyzer()
        analyzer.analyze_relationships()

        parents = analyzer.get_dependency_parents(self)
        children = analyzer.get_dependent_objects(self)

        return {
            'parents': parents,
            'children': children,
            'restoration_order': 'parents -> self -> children'
        }

    # Monkey patch the methods into SoftDeleteModel
    from core.models import SoftDeleteModel
    SoftDeleteModel.restore_instance = restore_instance
    SoftDeleteModel.bulk_cascade_restore = bulk_cascade_restore
    SoftDeleteModel.get_restoration_dependencies = get_restoration_dependencies


# Initialize the enhanced restoration system
add_cascade_restore_methods()
