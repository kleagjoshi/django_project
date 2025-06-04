from django.db import transaction
from django.shortcuts import get_object_or_404
from cms_api.models import Material, Group
from .material_vm import (
    MaterialVM, MaterialGetVM, MaterialCreateVM, MaterialUpdateVM
)


class MaterialsService:
    @staticmethod
    def add_material(material_data, group_id):
        """
        Add a new material to a group

        Args:
            material_data: Dict containing material data
            group_id: The group ID to add the material to

        Returns:
            bool: True if successful, False if group doesn't exist
        """
        # Create combined data for validation
        combined_data = {**material_data, 'group_id': group_id}

        # Validate input data
        serializer = MaterialCreateVM(data=combined_data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        # Check if the group exists
        if not Group.objects.filter(id=group_id).exists():
            return False

        try:
            # Create the material
            material = Material.objects.create(
                topic=validated_data['topic'],
                description=validated_data['description'],
                week=validated_data['week'],
                link=validated_data['link'],
                group_id=group_id
            )
            return True

        except Exception:
            return False

    @staticmethod
    def update_material_by_id(material_data, material_id):
        """
        Update an existing material

        Args:
            material_data: Dict containing updated material data
            material_id: The material ID to update

        Returns:
            bool: True if successful, False otherwise
        """
        # Validate input data
        serializer = MaterialUpdateVM(data=material_data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        try:
            material = Material.objects.get(id=material_id)
            material.topic = validated_data['topic']
            material.description = validated_data['description']
            material.week = validated_data['week']
            material.link = validated_data['link']
            material.save()
            return True

        except Material.DoesNotExist:
            return False

    @staticmethod
    def get_all_materials():
        """
        Get all materials

        Returns:
            List[dict]: List of material data in MaterialGetVM format
        """
        materials = Material.objects.all()
        return MaterialsService._build_material_view_models(materials)

    @staticmethod
    def get_material_by_id(material_id):
        """
        Get a specific material by ID

        Args:
            material_id: The material ID

        Returns:
            dict: Material data in MaterialGetVM format or None if not found
        """
        try:
            material = Material.objects.get(id=material_id)
            material_view_models = MaterialsService._build_material_view_models([material])
            return material_view_models[0] if material_view_models else None

        except Material.DoesNotExist:
            return None

    @staticmethod
    def get_all_materials_by_group_id(group_id):
        """
        Get all materials for a specific group

        Args:
            group_id: The group ID

        Returns:
            List[dict]: List of material data in MaterialGetVM format
        """
        materials = Material.objects.filter(group_id=group_id)
        return MaterialsService._build_material_view_models(materials)

    @staticmethod
    def delete_material_by_id(material_id):
        """
        Delete a material by ID

        Args:
            material_id: The material ID to delete

        Returns:
            bool: True if successful, False if material not found
        """
        try:
            material = Material.objects.get(id=material_id)
            material.delete()
            return True

        except Material.DoesNotExist:
            return False

    @staticmethod
    def _build_material_view_models(materials):
        """
        Helper method to build material view models from queryset

        Args:
            materials: QuerySet of Material objects

        Returns:
            List[dict]: List of material data in MaterialGetVM format
        """
        material_view_models = []

        for material in materials:
            material_view_models.append({
                'id': material.id,
                'topic': material.topic,
                'description': material.description,
                'week': material.week,
                'link': material.link
            })

        return material_view_models

    @staticmethod
    def get_materials_by_week(week_number):
        """
        Get all materials for a specific week

        Args:
            week_number: The week number

        Returns:
            List[dict]: List of material data in MaterialGetVM format
        """
        materials = Material.objects.filter(week=week_number)
        return MaterialsService._build_material_view_models(materials)

    @staticmethod
    def search_materials(topic=None):
        """
        Search materials by topic

        Args:
            topic: Topic to search for (optional)

        Returns:
            List[dict]: List of matching material data in MaterialGetVM format
        """
        if topic:
            materials = Material.objects.filter(topic__icontains=topic)
        else:
            materials = Material.objects.all()

        return MaterialsService._build_material_view_models(materials)