from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.http import HttpResponse
from django.db.models import Q
from datetime import datetime, timedelta
import io
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from .models import (
    CostCenter, AccountingPeriod, FinancialTransaction, 
    Budget, FinancialKPI, CashFlowStatement, FinancialReport
)
from .serializers import (
    CostCenterSerializer, AccountingPeriodSerializer, FinancialTransactionSerializer,
    BudgetSerializer, FinancialKPISerializer, CashFlowStatementSerializer,
    FinancialReportSerializer, ProfitLossRequestSerializer, BudgetVarianceRequestSerializer,
    CashFlowRequestSerializer, CostCenterAnalysisRequestSerializer, 
    FinancialTrendsRequestSerializer, ReportGenerationRequestSerializer
)
from .services import FinancialAnalyticsService


class CostCenterViewSet(viewsets.ModelViewSet):
    """ViewSet for cost center management"""
    queryset = CostCenter.objects.all()
    serializer_class = CostCenterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = CostCenter.objects.all()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset.order_by('code')


class AccountingPeriodViewSet(viewsets.ModelViewSet):
    """ViewSet for accounting period management"""
    queryset = AccountingPeriod.objects.all()
    serializer_class = AccountingPeriodSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = AccountingPeriod.objects.all()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset.order_by('-start_date')

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current accounting period"""
        today = timezone.now().date()
        current_period = AccountingPeriod.objects.filter(
            start_date__lte=today,
            end_date__gte=today,
            status='open'
        ).first()
        
        if current_period:
            serializer = self.get_serializer(current_period)
            return Response(serializer.data)
        else:
            return Response(
                {'error': 'No current accounting period found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class FinancialTransactionViewSet(viewsets.ModelViewSet):
    """ViewSet for financial transaction management"""
    queryset = FinancialTransaction.objects.all()
    serializer_class = FinancialTransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = FinancialTransaction.objects.all()
        
        # Filter by transaction type
        transaction_type = self.request.query_params.get('transaction_type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(
                transaction_date__gte=start_date,
                transaction_date__lte=end_date
            )
        
        # Filter by cost center
        cost_center_id = self.request.query_params.get('cost_center_id')
        if cost_center_id:
            queryset = queryset.filter(cost_center_id=cost_center_id)
        
        return queryset.order_by('-transaction_date', '-created_at')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class BudgetViewSet(viewsets.ModelViewSet):
    """ViewSet for budget management"""
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Budget.objects.all()
        
        # Filter by accounting period
        period_id = self.request.query_params.get('accounting_period_id')
        if period_id:
            queryset = queryset.filter(accounting_period_id=period_id)
        
        # Filter by budget type
        budget_type = self.request.query_params.get('budget_type')
        if budget_type:
            queryset = queryset.filter(budget_type=budget_type)
        
        return queryset.order_by('-accounting_period__start_date', 'name')

    @action(detail=True, methods=['post'])
    def calculate_variance(self, request, pk=None):
        """Calculate variance for a specific budget"""
        budget = self.get_object()
        budget.calculate_variance()
        serializer = self.get_serializer(budget)
        return Response(serializer.data)


class FinancialKPIViewSet(viewsets.ModelViewSet):
    """ViewSet for financial KPI management"""
    queryset = FinancialKPI.objects.all()
    serializer_class = FinancialKPISerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = FinancialKPI.objects.all()
        
        # Filter by accounting period
        period_id = self.request.query_params.get('accounting_period_id')
        if period_id:
            queryset = queryset.filter(accounting_period_id=period_id)
        
        # Filter by KPI type
        kpi_type = self.request.query_params.get('kpi_type')
        if kpi_type:
            queryset = queryset.filter(kpi_type=kpi_type)
        
        return queryset.order_by('-accounting_period__start_date', 'kpi_type')


class FinancialReportViewSet(viewsets.ModelViewSet):
    """ViewSet for financial report management"""
    queryset = FinancialReport.objects.all()
    serializer_class = FinancialReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = FinancialReport.objects.all()
        
        # Filter by report type
        report_type = self.request.query_params.get('report_type')
        if report_type:
            queryset = queryset.filter(report_type=report_type)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-generated_at')

    def perform_create(self, serializer):
        serializer.save(generated_by=self.request.user)


class FinancialAnalyticsViewSet(viewsets.ViewSet):
    """ViewSet for financial analytics and reporting"""
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.analytics_service = FinancialAnalyticsService()

    @action(detail=False, methods=['post'])
    def profit_loss_statement(self, request):
        """Generate profit and loss statement"""
        serializer = ProfitLossRequestSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            try:
                pl_statement = self.analytics_service.generate_profit_loss_statement(
                    start_date=data['start_date'],
                    end_date=data['end_date'],
                    cost_center_id=data.get('cost_center_id')
                )
                return Response(pl_statement)
            except Exception as e:
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def budget_variance_report(self, request):
        """Generate budget variance report"""
        serializer = BudgetVarianceRequestSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            try:
                variance_report = self.analytics_service.generate_budget_variance_report(
                    accounting_period_id=str(data['accounting_period_id'])
                )
                return Response(variance_report)
            except Exception as e:
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def calculate_kpis(self, request):
        """Calculate financial KPIs for a period"""
        serializer = BudgetVarianceRequestSerializer(data=request.data)  # Reuse for period_id
        if serializer.is_valid():
            data = serializer.validated_data
            try:
                kpis = self.analytics_service.calculate_financial_kpis(
                    accounting_period_id=str(data['accounting_period_id'])
                )
                return Response(kpis)
            except Exception as e:
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def cash_flow_statement(self, request):
        """Generate cash flow statement"""
        serializer = CashFlowRequestSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            try:
                cash_flow = self.analytics_service.generate_cash_flow_statement(
                    start_date=data['start_date'],
                    end_date=data['end_date']
                )
                return Response(cash_flow)
            except Exception as e:
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def cost_center_analysis(self, request):
        """Generate cost center analysis"""
        serializer = CostCenterAnalysisRequestSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            try:
                analysis = self.analytics_service.get_cost_center_analysis(
                    start_date=data['start_date'],
                    end_date=data['end_date']
                )
                return Response(analysis)
            except Exception as e:
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def financial_trends(self, request):
        """Get financial trends over time"""
        serializer = FinancialTrendsRequestSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            try:
                trends = self.analytics_service.get_financial_trends(
                    months=data.get('months', 12)
                )
                return Response(trends)
            except Exception as e:
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def dashboard_summary(self, request):
        """Get financial dashboard summary"""
        try:
            # Get current period
            today = timezone.now().date()
            current_period = AccountingPeriod.objects.filter(
                start_date__lte=today,
                end_date__gte=today,
                status='open'
            ).first()

            if not current_period:
                return Response(
                    {'error': 'No current accounting period found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            # Generate P&L for current period
            pl_statement = self.analytics_service.generate_profit_loss_statement(
                start_date=current_period.start_date,
                end_date=current_period.end_date
            )

            # Get KPIs
            kpis = self.analytics_service.calculate_financial_kpis(
                accounting_period_id=str(current_period.id)
            )

            # Get recent trends (last 6 months)
            trends = self.analytics_service.get_financial_trends(months=6)

            return Response({
                'current_period': {
                    'id': str(current_period.id),
                    'name': current_period.name,
                    'start_date': current_period.start_date.strftime('%Y-%m-%d'),
                    'end_date': current_period.end_date.strftime('%Y-%m-%d')
                },
                'profit_loss': pl_statement,
                'kpis': kpis,
                'trends': trends
            })

        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def export_report(self, request):
        """Export financial report to PDF or Excel"""
        serializer = ReportGenerationRequestSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            try:
                # Generate the report data based on type
                if data['report_type'] == 'profit_loss':
                    report_data = self.analytics_service.generate_profit_loss_statement(
                        start_date=data['start_date'],
                        end_date=data['end_date']
                    )
                elif data['report_type'] == 'budget_variance':
                    if not data.get('accounting_period_id'):
                        return Response(
                            {'error': 'accounting_period_id required for budget variance report'}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    report_data = self.analytics_service.generate_budget_variance_report(
                        accounting_period_id=str(data['accounting_period_id'])
                    )
                elif data['report_type'] == 'cash_flow':
                    report_data = self.analytics_service.generate_cash_flow_statement(
                        start_date=data['start_date'],
                        end_date=data['end_date']
                    )
                else:
                    return Response(
                        {'error': 'Unsupported report type'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Create report record
                report = FinancialReport.objects.create(
                    report_type=data['report_type'],
                    name=data['name'],
                    start_date=data['start_date'],
                    end_date=data['end_date'],
                    accounting_period_id=data.get('accounting_period_id'),
                    parameters=data.get('parameters', {}),
                    generated_by=request.user,
                    status='completed'
                )

                # For now, return the data (in a real implementation, you'd generate PDF/Excel)
                return Response({
                    'report_id': str(report.id),
                    'report_data': report_data,
                    'download_url': f'/api/financial/reports/{report.id}/download/'
                })

            except Exception as e:
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='reports/(?P<report_id>[^/.]+)/download')
    def download_report(self, request, report_id=None):
        """Download generated report file"""
        try:
            report = FinancialReport.objects.get(id=report_id)
            
            # For demonstration, create a simple PDF
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            
            # Add report content
            p.drawString(100, 750, f"Financial Report: {report.name}")
            p.drawString(100, 730, f"Period: {report.start_date} to {report.end_date}")
            p.drawString(100, 710, f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M')}")
            p.drawString(100, 690, f"Report Type: {report.get_report_type_display()}")
            
            p.showPage()
            p.save()
            
            buffer.seek(0)
            response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{report.name}.pdf"'
            
            return response
            
        except FinancialReport.DoesNotExist:
            return Response(
                {'error': 'Report not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )