import frappe
from erpnext.controllers.status_updater import validate_status
from erpnext.stock.doctype.material_request.material_request import MaterialRequest
from frappe import _

from dermagroup_lab.purchasing.enums import ApprovalStatus


class CustomMaterialRequest(MaterialRequest):
	"""
	Sobrescribe para permitir valores personalizados en el campo status
	"""

	def validate(self):
		"""
		Sobrescribe validate para validar con los estados personalizados
		"""
		# Establecer status inicial si no existe
		if not self.status and self.docstatus == 0:
			self.status = ApprovalStatus.PENDING_APPROVAL.value

		# Validar que el status sea uno de los valores permitidos
		if self.status:
			allowed_statuses = [approval_status.value for approval_status in ApprovalStatus]
			validate_status(self.status, allowed_statuses)

		# Guardar el status actual antes de ejecutar validación del padre
		original_status = self.status

		# Ejecutar la validación original (sin llamar a validate para evitar recursión)
		# En su lugar, llamamos directamente a los métodos necesarios
		self.validate_qty()
		if self.material_request_type == "Material Transfer":
			self.validate_for_material_transfer()

		# Restaurar el status personalizado
		self.status = original_status

		# Establecer título como en el core
		self.set_title()

	def before_save(self):
		"""
		Asegurar que el status se establezca antes de guardar
		"""
		if not self.status and self.docstatus == 0:
			self.status = ApprovalStatus.PENDING_APPROVAL.value

	def set_status(self, update=False, status=None, update_modified=True):
		"""
		Sobrescribe set_status para usar valores personalizados
		"""
		# Si ya tiene status y queremos actualizar, mantener el actual
		if self.status and update:
			status = self.status
		# Si se pasa un status específico, usarlo
		elif status:
			self.status = status
		# Si no hay status, establecer el inicial
		elif not self.status:
			status = ApprovalStatus.PENDING_APPROVAL.value
			self.status = status

		# Actualizar en la base de datos si se solicita
		if update:
			self.db_set("status", status, update_modified=update_modified)

	def on_submit(self):
		"""
		Validar que esté aprobado antes de enviar y mantener el status
		"""
		# Validar que el status sea "Approved" antes de permitir submit
		if self.status != ApprovalStatus.APPROVED.value:
			frappe.throw(
				_("Material Request must be Approved before submitting. Current status: {0}").format(
					self.status
				)
			)

		# Guardar el status antes del submit
		current_status = self.status

		# Ejecutar el submit original
		super().on_submit()

		# Restaurar el status después del submit
		if current_status:
			self.db_set("status", current_status)
			self.status = current_status

	def set_title(self):
		"""
		Replica del core: título = "<Tipo> Request for <primeros 3 items>", máx 100 chars.
		"""
		if not self.title:
			items = ", ".join([d.item_name for d in self.items][:3])
			self.title = _("{0} Request for {1}").format(_(self.material_request_type), items)[:100]

	def on_cancel(self):
		"""
		Actualizar el status al cancelar
		"""
		super().on_cancel()
		self.status = ApprovalStatus.CANCELLED.value
		self.db_set("status", ApprovalStatus.CANCELLED.value)
