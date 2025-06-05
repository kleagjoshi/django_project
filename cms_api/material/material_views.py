from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from cms_api.models import Material, Lecturer, Student
from cms_api.permissions import CanManageMaterials
from .material_service import MaterialsService
from .material_vm import (
    MaterialVM, MaterialGetVM, MaterialCreateVM, MaterialUpdateVM
)
from cms_api.serializers import MaterialSerializer


class MaterialViewSet(viewsets.ModelViewSet):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    permission_classes = [CanManageMaterials]

    def get_queryset(self):
        """
        Filter queryset based on user role
        """
        if self.request.user.is_staff:
            # Admin can see all materials
            return Material.objects.all()
        
        try:
            # Lecturer can see materials for their groups
            lecturer = Lecturer.objects.get(user=self.request.user)
            return Material.objects.filter(
                group__course_lecturer__lecturer=lecturer
            )
        except Lecturer.DoesNotExist:
            pass
        
        try:
            # Students can see materials for groups they're enrolled in
            student = Student.objects.get(user=self.request.user)
            return Material.objects.filter(
                group__group_students__student=student
            ).distinct()
        except Student.DoesNotExist:
            pass
        
        # Default: empty queryset if user has no role
        return Material.objects.none()

    @extend_schema(
        request=MaterialCreateVM,
        responses={201: MaterialGetVM},
        description="Create a new material for a group"
    )
    def create(self, request):
        """
        Add a new material
        """
        try:
            group_id = request.data.get('group_id')
            if not group_id:
                return Response(
                    {'error': 'group_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Extract material data (excluding group_id)
            material_data = {
                'topic': request.data.get('topic'),
                'description': request.data.get('description'),
                'week': request.data.get('week'),
                'link': request.data.get('link')
            }

            result = MaterialsService.add_material(material_data, group_id)
            if result['success']:
                # Get the created material to return
                if 'material_id' in result:
                    material_data = MaterialsService.get_material_by_id(result['material_id'])
                    if material_data:
                        return Response(material_data, status=status.HTTP_201_CREATED)
                
                return Response(
                    {'success': True, 'message': result['message']},
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {'error': result['message']},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: MaterialGetVM(many=True)},
        description="Get all materials"
    )
    def list(self, request):
        """
        Get all materials
        """
        materials = MaterialsService.get_all_materials()
        return Response(materials)

    @extend_schema(
        responses={200: MaterialGetVM},
        description="Get a specific material by ID"
    )
    def retrieve(self, request, pk=None):
        """
        Get material by ID
        """
        material_data = MaterialsService.get_material_by_id(pk)
        if material_data:
            return Response(material_data)
        else:
            return Response(
                {'error': 'Material not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        request=MaterialUpdateVM,
        responses={200: MaterialGetVM},
        description="Update material information"
    )
    def update(self, request, pk=None):
        """
        Update material 
        """
        try:
            result = MaterialsService.update_material_by_id(request.data, pk)
            if result['success']:
                material_data = MaterialsService.get_material_by_id(pk)
                if material_data:
                    return Response(material_data)
                else:
                    return Response(
                        {'success': True, 'message': result['message']}
                    )
            else:
                return Response(
                    {'error': result['message']},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {'success': {'type': 'boolean'}}}},
        description="Delete a material"
    )
    def destroy(self, request, pk=None):
        """
        Delete material 
        """
        result = MaterialsService.delete_material_by_id(pk)
        if result['success']:
            return Response({'success': True, 'message': result['message']})
        else:
            return Response(
                {'error': result['message']},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: MaterialGetVM(many=True)},
        description="Get all materials for a specific group",
        parameters=[
            OpenApiParameter(
                name='group_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID of the group'
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def by_group(self, request):
        """
        Get materials by group
        """
        group_id = request.query_params.get('group_id')
        if not group_id:
            return Response(
                {'error': 'group_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            materials = MaterialsService.get_all_materials_by_group_id(group_id)
            return Response(materials)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: MaterialGetVM(many=True)},
        description="Get all materials for a specific week",
        parameters=[
            OpenApiParameter(
                name='week',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Week number'
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def by_week(self, request):
        """
        Get materials by week - additional functionality
        """
        week = request.query_params.get('week')
        if not week:
            return Response(
                {'error': 'week parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            materials = MaterialsService.get_materials_by_week(int(week))
            return Response(materials)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: MaterialGetVM(many=True)},
        description="Search materials by topic",
        parameters=[
            OpenApiParameter(
                name='topic',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Topic to search for',
                required=False
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search materials - additional functionality
        """
        topic = request.query_params.get('topic', '')

        try:
            materials = MaterialsService.search_materials(
                topic=topic if topic else None
            )
            return Response(materials)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {
            'total_materials': {'type': 'integer'},
            'materials_by_week': {'type': 'object'},
            'average_materials_per_group': {'type': 'number'},
            'most_common_topics': {'type': 'array'}
        }}},
        description="Get material statistics - Only accessible by lecturers and admin"
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get material statistics - Only accessible by lecturers and admin
        """
        # Check if user is lecturer or admin
        if not request.user.is_staff:
            try:
                Lecturer.objects.get(user=request.user)
            except Lecturer.DoesNotExist:
                return Response(
                    {'error': 'Only lecturers and administrators can access material statistics'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        try:
            all_materials = MaterialsService.get_all_materials()

            if not all_materials:
                return Response({
                    'total_materials': 0,
                    'materials_by_week': {},
                    'average_materials_per_group': 0,
                    'most_common_topics': []
                })

            total_materials = len(all_materials)

            # Count materials by week
            materials_by_week = {}
            group_counts = {}
            topic_counts = {}

            for material in all_materials:
                # Count by week
                week_key = f"Week {material['week']}"
                materials_by_week[week_key] = materials_by_week.get(week_key, 0) + 1

                # Count by topic (for most common topics)
                topic = material['topic']
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

            # Get most common topics (top 5)
            most_common_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            most_common_topics = [{'topic': topic, 'count': count} for topic, count in most_common_topics]

            # Calculate average materials per group (this would need group data)
            # For now, we'll use a simplified calculation
            unique_groups = len(set(material.get('group_id', 0) for material in all_materials))
            average_materials_per_group = total_materials / unique_groups if unique_groups > 0 else 0

            return Response({
                'total_materials': total_materials,
                'materials_by_week': materials_by_week,
                'average_materials_per_group': round(average_materials_per_group, 2),
                'most_common_topics': most_common_topics
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )