from django.db import transaction
from django.shortcuts import get_object_or_404
from cms_api.models import Material, Group
from cms_api.enums import GroupStatus
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
            dict: Result with success status and message
        """
        # Create combined data for validation
        combined_data = {**material_data, 'group_id': group_id}

        # Validate input data
        serializer = MaterialCreateVM(data=combined_data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        # Check if the group exists and get its status
        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            return {
                'success': False,
                'message': 'Group not found'
            }

        # Check if group status allows material modifications
        status_check = MaterialsService._check_group_status_for_material_modification(group)
        if not status_check['allowed']:
            return status_check

        try:
            # Create the material
            material = Material.objects.create(
                topic=validated_data['topic'],
                description=validated_data['description'],
                week=validated_data['week'],
                link=validated_data['link'],
                group_id=group_id
            )
            return {
                'success': True,
                'message': 'Material successfully added to group',
                'material_id': material.id
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to add material: {str(e)}'
            }

    @staticmethod
    def update_material_by_id(material_data, material_id):
        """
        Update an existing material

        Args:
            material_data: Dict containing updated material data
            material_id: The material ID to update

        Returns:
            dict: Result with success status and message
        """
        # Validate input data
        serializer = MaterialUpdateVM(data=material_data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        try:
            material = Material.objects.select_related('group').get(id=material_id)
        except Material.DoesNotExist:
            return {
                'success': False,
                'message': 'Material not found'
            }

        # Check if group status allows material modifications
        status_check = MaterialsService._check_group_status_for_material_modification(material.group)
        if not status_check['allowed']:
            return status_check

        try:
            material.topic = validated_data['topic']
            material.description = validated_data['description']
            material.week = validated_data['week']
            material.link = validated_data['link']
            material.save()
            
            return {
                'success': True,
                'message': 'Material successfully updated'
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to update material: {str(e)}'
            }

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
            dict: Result with success status and message
        """
        try:
            material = Material.objects.select_related('group').get(id=material_id)
        except Material.DoesNotExist:
            return {
                'success': False,
                'message': 'Material not found'
            }

        # Check if group status allows material modifications
        status_check = MaterialsService._check_group_status_for_material_modification(material.group)
        if not status_check['allowed']:
            return status_check

        try:
            material.delete()
            return {
                'success': True,
                'message': 'Material successfully deleted'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to delete material: {str(e)}'
            }

    @staticmethod
    def _check_group_status_for_material_modification(group):
        """
        Helper method to check if group status allows material modifications

        Args:
            group: Group object

        Returns:
            dict: Result with allowed status and message
        """
        if group.status != GroupStatus.ONGOING:
            status_name = dict(GroupStatus.choices).get(group.status, 'Unknown')
            return {
                'success': False,
                'allowed': False,
                'message': f'Cannot modify materials for groups with status "{status_name}". Materials can only be added or edited for ongoing groups.'
            }
        
        return {
            'success': True,
            'allowed': True,
            'message': 'Group status allows material modifications'
        }

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